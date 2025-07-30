import pytest
import shutil
from pathlib import Path
import os

from bashvar_sentry import (
    source_and_get_vars,
    ScriptNotFoundError,
    BashScriptError,
    BashExecutableNotFoundError,
)

ALL_TYPES_SCRIPT_CONTENT = """
#!/bin/bash
ls /tmp
SIMPLE_STRING="Hello World"
STRING_WITH_QUOTES="A value with 'single' and \\"double\\" quotes."
EXPORTED_VAR="This was exported"
export EXPORTED_VAR
FRUITS=("apple" "banana split" "cherry")
declare -A CONFIG
CONFIG["host"]="localhost"
CONFIG["port"]="8080"
CONFIG['user name']="admin-user"
"""


@pytest.fixture
def create_script(tmp_path: Path):
    def _create_script(filename: str, content: str) -> Path:
        script_path = tmp_path / filename
        script_path.write_text(content)
        script_path.chmod(0o755)
        return script_path

    return _create_script


def test_parses_all_variable_types(create_script):
    script_path = create_script("all_types.sh", ALL_TYPES_SCRIPT_CONTENT)
    variables = source_and_get_vars(script_path)

    expected = {
        "SIMPLE_STRING": "Hello World",
        "STRING_WITH_QUOTES": "A value with 'single' and \"double\" quotes.",
        "EXPORTED_VAR": "This was exported",
        "FRUITS": ["apple", "banana split", "cherry"],
        "CONFIG": {
            "host": "localhost",
            "port": "8080",
            "user name": "admin-user",
        },
    }

    assert all(item in variables.items() for item in expected.items())


def test_filters_for_target_vars(create_script):
    script_path = create_script("all_types.sh", ALL_TYPES_SCRIPT_CONTENT)
    variables = source_and_get_vars(
        script_path, target_vars=["SIMPLE_STRING", "CONFIG"]
    )

    assert "SIMPLE_STRING" in variables
    assert "CONFIG" in variables
    assert "FRUITS" not in variables


def test_raises_script_not_found_error():
    with pytest.raises(ScriptNotFoundError):
        source_and_get_vars("./this_file_does_not_exist_12345.sh")


def test_raises_bash_script_error_on_fatal_syntax(create_script):
    script_path = create_script("fatal.sh", "if; then")
    with pytest.raises(BashScriptError) as excinfo:
        source_and_get_vars(script_path)
    assert excinfo.value.exit_code != 0
    assert "syntax error" in excinfo.value.stderr.lower()


def test_raises_bash_executable_not_found(monkeypatch, create_script):
    dummy_script_path = create_script("dummy.sh", "VAR=1").resolve()
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    original_is_file = Path.is_file

    def mock_is_file(self):
        if self == dummy_script_path:
            return original_is_file(self)
        return False

    monkeypatch.setattr(Path, "is_file", mock_is_file)

    with pytest.raises(BashExecutableNotFoundError):
        source_and_get_vars(dummy_script_path)


def test_empty_script_returns_no_user_vars(create_script):
    script_path = create_script("empty.sh", "#!/bin/bash\n# No variables here")
    variables = source_and_get_vars(script_path)
    assert "SIMPLE_STRING" not in variables
    assert "FRUITS" not in variables


def test_extra_env_variable_is_injected(create_script):
    script_path = create_script(
        "env_var.sh", '#!/bin/bash\nMYVAR="$MYVAR"\ndeclare MYVAR'
    )
    os.chmod(script_path, 0o755)
    vars = source_and_get_vars(script_path, extra_env={"MYVAR": "visible"})
    assert vars.get("MYVAR") == "visible"


def test_additional_args_passed_through(create_script):
    script_path = create_script(
        "args_test.sh",
        """
#!/bin/bash
# inspector will pass $@ after script path
ARG1=$1
ARG2=$2
declare ARG1
declare ARG2
""",
    )
    os.chmod(script_path, 0o755)
    vars = source_and_get_vars(script_path, additional_args=["foo", "bar"])
    assert vars.get("ARG1") == "foo"
    assert vars.get("ARG2") == "bar"


# Test all sandboxed methods
#
SANDBOX_SCRIPT = """#!/bin/bash
MYVAR="sandboxed"
declare MYVAR
"""


@pytest.mark.skipif(
    os.geteuid() != 0 or not Path("/usr/sbin/chroot").is_file(),
    reason="chroot requires root and /usr/sbin/chroot",
)
def test_sandbox_method_chroot(create_script):
    script_path = create_script("chroot_test.sh", SANDBOX_SCRIPT)
    variables = source_and_get_vars(script_path, sandbox_method="chroot", jail_dir="/")
    assert variables.get("MYVAR") == "sandboxed"


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bwrap not available")
def test_sandbox_method_bwrap(create_script):
    script_path = create_script("bwrap_test.sh", SANDBOX_SCRIPT)
    variables = source_and_get_vars(script_path, sandbox_method="bwrap", jail_dir="/")
    assert variables.get("MYVAR") == "sandboxed"


@pytest.mark.skipif(
    shutil.which("fakechroot") is None, reason="fakechroot not available"
)
def test_sandbox_method_fakechroot(create_script):
    script_path = create_script("fakechroot_test.sh", SANDBOX_SCRIPT)
    variables = source_and_get_vars(
        script_path, sandbox_method="fakechroot", jail_dir="/"
    )
    assert variables.get("MYVAR") == "sandboxed"


def test_sandbox_method_empty(create_script):
    script_path = create_script("empty_test.sh", SANDBOX_SCRIPT)
    variables = source_and_get_vars(script_path, sandbox_method="empty", jail_dir="/")
    assert variables.get("MYVAR") == "sandboxed"
