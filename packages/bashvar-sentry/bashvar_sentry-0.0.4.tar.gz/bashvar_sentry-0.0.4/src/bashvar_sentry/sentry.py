import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

try:
    from importlib.resources import files, as_file
except ImportError:
    from importlib_resources import files, as_file  # type: ignore

from .exceptions import (
    BashScriptError,
    ScriptNotFoundError,
    ParsingError,
    BashExecutableNotFoundError,
)

DECLARE_LINE_RE = re.compile(r"declare -([a-zA-Z-]+) ([^=]+)=(.*)", re.DOTALL)
ITEM_SPLIT_RE = re.compile(
    r'(\[[^]]+\]=)(?:"((?:\\.|[^"])*)"|\'((?:\\.|[^\'])*)\'|[^\s]+)'
)


CHROOT_PATH = "/usr/sbin/chroot"
BWRAP_PATH = shutil.which("bwrap")
FAKECHROOT_PATH = shutil.which("fakechroot")


def _find_bash_executable() -> str:
    bash_path = shutil.which("bash")
    if bash_path:
        return bash_path
    for path in ["/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]:
        if Path(path).is_file():
            return path
    raise BashExecutableNotFoundError(
        "The 'bash' executable was not found in the system's PATH or common locations."
    )


def _parse_bash_value(value_str: str) -> Any:
    try:
        unquoted = shlex.split(value_str)
        if len(unquoted) == 1:
            return unquoted[0]
        return value_str
    except ValueError:
        return value_str


def _parse_declare_output(output: str) -> Dict[str, Any]:
    variables: Dict[str, Any] = {}
    for line in output.strip().split("\n"):
        if not line.startswith("declare -"):
            continue
        match = DECLARE_LINE_RE.match(line)
        if not match:
            continue
        flags, var_name, value_part = match.groups()
        try:
            if "a" in flags:
                content = value_part.strip()[1:-1]
                arr = []
                for item_match in ITEM_SPLIT_RE.finditer(content):
                    val_str = item_match.group(0).split("=", 1)[1]
                    arr.append(_parse_bash_value(val_str))
                variables[var_name] = arr
            elif "A" in flags:
                content = value_part.strip()[1:-1]
                assoc_arr = {}
                for item_match in ITEM_SPLIT_RE.finditer(content):
                    key_str, val_str = item_match.group(0).split("=", 1)
                    key = key_str.strip()[1:-1]
                    assoc_arr[_parse_bash_value(key)] = _parse_bash_value(val_str)
                variables[var_name] = assoc_arr
            else:
                variables[var_name] = _parse_bash_value(value_part)
        except Exception as e:
            raise ParsingError(
                f"Failed to parse variable '{var_name}' from line: {line}"
            ) from e
    return variables


def _supports_chroot() -> bool:
    return os.geteuid() == 0 and Path(CHROOT_PATH).is_file()


def _supports_bwrap() -> bool:
    return BWRAP_PATH is not None


def _supports_fakechroot() -> bool:
    return FAKECHROOT_PATH is not None


def _wrap_with_sandbox(cmd: List[str], method: str, jail_dir: str) -> List[str]:
    if method == "chroot" and _supports_chroot():
        return [CHROOT_PATH, jail_dir] + cmd
    elif method == "bwrap" and _supports_bwrap():
        return [BWRAP_PATH, "--ro-bind", jail_dir, "/", "--chdir", "/"] + cmd
    elif method == "fakechroot" and _supports_fakechroot():
        return [FAKECHROOT_PATH, "chroot", jail_dir] + cmd
    elif method == "empty":
        return cmd
    else:
        raise RuntimeError(
            f"Requested sandbox method '{method}' is unavailable on this system."
        )


def source_and_get_vars(
    script_path: Union[str, Path],
    target_vars: Optional[List[str]] = None,
    sandbox_method: str = "auto",
    jail_dir: Optional[str] = None,
    extra_env: Optional[Dict[str, str]] = None,
    additional_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    script_file = Path(script_path).resolve()
    if not script_file.is_file():
        raise ScriptNotFoundError(
            f"The script '{script_path}' was not found at '{script_file}'"
        )

    bash_executable = _find_bash_executable()

    harness_ref = files("bashvar_sentry.resources").joinpath("inspector.sh")
    with as_file(harness_ref) as inspector_path:
        inner_cmd = [
            bash_executable,
            str(inspector_path),
            bash_executable,
            str(script_file),
        ]
        if additional_args:
            inner_cmd += additional_args

        if sandbox_method == "auto":
            if _supports_chroot():
                sandbox_method = "chroot"
            elif _supports_bwrap():
                sandbox_method = "bwrap"
            elif _supports_fakechroot():
                sandbox_method = "fakechroot"
            else:
                sandbox_method = "empty"

        jail = jail_dir or "/"
        full_cmd = _wrap_with_sandbox(inner_cmd, sandbox_method, jail)

        env = os.environ.copy()
        if sandbox_method == "empty":
            env["PATH"] = ""
        if extra_env:
            env.update(extra_env)

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                env=env,
            )
        except subprocess.CalledProcessError as e:
            raise BashScriptError(
                f"The script '{script_path}' failed to execute.",
                stderr=e.stderr,
                exit_code=e.returncode,
            ) from e

    all_vars = _parse_declare_output(result.stdout)
    if target_vars:
        return {k: v for k, v in all_vars.items() if k in target_vars}
    return all_vars
