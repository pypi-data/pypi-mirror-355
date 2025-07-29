# src/bashvar_sentry/sentry.py

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# In Python 3.9+, we can use files(), but for broader compatibility,
# we will use the older importlib.resources API.
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

# Regex to parse a 'declare -p' line. It captures:
# 1. Declaration flags (e.g., 'x', 'a', 'A')
# 2. Variable name
# 3. The value part of the assignment
DECLARE_LINE_RE = re.compile(r"declare -([a-zA-Z-]+) ([^=]+)=(.*)", re.DOTALL)

# A more robust regex for splitting array/map content key-value pairs
# It correctly handles escaped characters and quotes inside values.
# Example: `[0]="value \"with\" quotes" [1]="another"`
ITEM_SPLIT_RE = re.compile(
    r'(\[[^]]+\]=)(("(\\"|[^"])*")|(\'(\\\'|[^\\\'])*\')|[^\s]+)'
)


# Add this new function inside sentry.py, before source_and_get_vars


def _find_bash_executable() -> str:
    """
    Finds the absolute path to the bash executable, respecting PATH and
    checking common fallbacks.
    """
    # 1. Respect the system's PATH first. This is the most reliable method.
    bash_path = shutil.which("bash")
    if bash_path:
        return bash_path

    # 2. If not in PATH, check common locations as a fallback.
    common_paths = ["/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]
    for path in common_paths:
        if Path(path).is_file():
            return path

    # 3. If it's still not found, raise a specific error.
    raise BashExecutableNotFoundError(
        "The 'bash' executable was not found in the system's PATH or in common "
        "locations (/bin/bash, /usr/bin/bash). Please ensure bash is installed."
    )


def _parse_bash_value(value_str: str) -> Any:
    """Safely parses a shell-quoted string into a Python value."""
    # Using shlex.split is a robust way to unquote a single shell token.
    # It handles nested quotes and escapes correctly.
    try:
        # If the string is not quoted, shlex will return it as is.
        # If it is quoted, it will unquote it.
        unquoted = shlex.split(value_str)
        if len(unquoted) == 1:
            return unquoted[0]
        # This case handles values with spaces that weren't quoted, e.g., `(a b c)`
        return value_str
    except ValueError:
        # Fallback for complex cases that shlex might not handle
        return value_str


def _parse_declare_output(output: str) -> Dict[str, Any]:
    """Parses the full output of 'declare -p' into a Python dictionary."""
    variables: Dict[str, Any] = {}
    lines = output.strip().split("\n")

    for line in lines:
        if not line.startswith("declare -"):
            continue

        match = DECLARE_LINE_RE.match(line)
        if not match:
            continue

        flags, var_name, value_part = match.groups()

        try:
            # Handle Indexed Arrays (declare -a)
            if "a" in flags:
                # Value is in the form ([0]="val1" [1]="val2")
                content = value_part.strip()[1:-1]
                arr = []
                # Use regex to split items respecting quotes
                for item_match in ITEM_SPLIT_RE.finditer(content):
                    full_item = item_match.group(0)
                    # The value is everything after the first '='
                    val_str = full_item.split("=", 1)[1]
                    arr.append(_parse_bash_value(val_str))
                variables[var_name] = arr

            # Handle Associative Arrays (declare -A)
            elif "A" in flags:
                # Value is in the form ([key1]="val1" [key2]="val2")
                content = value_part.strip()[1:-1]
                assoc_arr = {}
                # Use regex to split items respecting quotes
                for item_match in ITEM_SPLIT_RE.finditer(content):
                    full_item = item_match.group(0)
                    key_str, val_str = full_item.split("=", 1)
                    key = key_str.strip()[1:-1]  # Remove brackets
                    assoc_arr[_parse_bash_value(key)] = _parse_bash_value(val_str)
                variables[var_name] = assoc_arr

            # Handle simple string/number variables
            else:
                variables[var_name] = _parse_bash_value(value_part)

        except Exception as e:
            # This helps debug parsing issues with complex variable declarations
            raise ParsingError(
                f"Failed to parse variable '{var_name}' from line: {line}"
            ) from e

    return variables


def source_and_get_vars(
    script_path: Union[str, Path], target_vars: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Safely sources a bash script in a sandboxed environment and extracts its variables.

    Args:
        script_path: Absolute or relative path to the bash script to source.
        target_vars: An optional list of specific variable names to retrieve.
                     If None, all variables declared by the script are returned.

    Returns:
        A dictionary mapping variable names to their values.
        Bash indexed arrays are returned as Python lists.
        Bash associative arrays are returned as Python dictionaries.

    Raises:
        ScriptNotFoundError: If the script_path does not exist.
        BashScriptError: If the script exits with a non-zero status code.
        ParsingError: If the script output cannot be parsed.
    """
    script_file = Path(script_path).resolve()
    if not script_file.is_file():
        raise ScriptNotFoundError(
            f"The script '{script_path}' was not found at '{script_file}'"
        )

    bash_executable = _find_bash_executable()

    # Use importlib.resources to reliably find our packaged inspector script
    # This context manager handles temporary file creation if the resource is in a zip
    harness_ref = files("bashvar_sentry.resources").joinpath("inspector.sh")
    with as_file(harness_ref) as inspector_path:
        cmd = [bash_executable, str(inspector_path), bash_executable, str(script_file)]

        # The Sandbox: Create a minimal environment with an empty PATH.
        # This is the core of the security model, preventing execution of external commands.
        sandboxed_env = os.environ.copy()
        sandboxed_env["PATH"] = ""

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,  # Raises CalledProcessError on non-zero exit codes
                encoding="utf-8",
                env=sandboxed_env,
            )
        except subprocess.CalledProcessError as e:
            raise BashScriptError(
                f"The script '{script_path}' failed to execute.",
                stderr=e.stderr,
                exit_code=e.returncode,
            ) from e

    all_vars = _parse_declare_output(result.stdout)

    if target_vars:
        # Filter for the requested variables
        return {k: v for k, v in all_vars.items() if k in target_vars}

    return all_vars
