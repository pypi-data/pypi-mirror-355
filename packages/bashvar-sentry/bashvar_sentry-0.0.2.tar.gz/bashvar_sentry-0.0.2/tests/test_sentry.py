import pytest
import shutil
from pathlib import Path

from bashvar_sentry import (
    source_and_get_vars,
    ScriptNotFoundError,
    BashScriptError,
    BashExecutableNotFoundError,
)

# A comprehensive script that tests all variable types and the sandbox
# by including a command that would normally be available.
ALL_TYPES_SCRIPT_CONTENT = """
#!/bin/bash

# This command should fail because 'ls' is not in the sandboxed PATH
ls /tmp

# --- Variable Definitions ---
SIMPLE_STRING="Hello World"
STRING_WITH_QUOTES="A value with 'single' and \\"double\\" quotes."
EXPORTED_VAR="This was exported"
export EXPORTED_VAR

# Indexed Array
FRUITS=("apple" "banana split" "cherry")

# Associative Array
declare -A CONFIG
CONFIG["host"]="localhost"
CONFIG["port"]="8080"
CONFIG['user name']="admin-user"
"""


@pytest.fixture
def create_script(tmp_path: Path):
    """A pytest fixture to create a script file in a temporary directory."""

    def _create_script(filename: str, content: str) -> Path:
        script_path = tmp_path / filename
        script_path.write_text(content)
        script_path.chmod(0o755)
        return script_path

    return _create_script


def test_parses_all_variable_types(create_script):
    """
    Tests that strings, indexed arrays, and associative arrays are all parsed correctly.
    Also implicitly tests that the 'ls' command fails without stopping the script.
    """
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

    # We can't guarantee the order of other shell variables, so check our expected ones.
    assert all(item in variables.items() for item in expected.items())
    assert variables["SIMPLE_STRING"] == "Hello World"
    assert len(variables["FRUITS"]) == 3
    assert variables["CONFIG"]["user name"] == "admin-user"


def test_filters_for_target_vars(create_script):
    """Tests that the target_vars argument correctly filters the result."""
    script_path = create_script("all_types.sh", ALL_TYPES_SCRIPT_CONTENT)
    variables = source_and_get_vars(
        script_path, target_vars=["SIMPLE_STRING", "CONFIG"]
    )

    expected = {
        "SIMPLE_STRING": "Hello World",
        "CONFIG": {
            "host": "localhost",
            "port": "8080",
            "user name": "admin-user",
        },
    }
    assert variables == expected


def test_raises_script_not_found_error():
    """Tests that the correct exception is raised for a non-existent file."""
    with pytest.raises(ScriptNotFoundError):
        source_and_get_vars("./this_file_does_not_exist_12345.sh")


def test_raises_bash_script_error_on_fatal_syntax(create_script):
    """Tests that a fatal script error (like a syntax error) raises BashScriptError."""
    fatal_script_content = "if; then"  # Invalid bash syntax
    script_path = create_script("fatal.sh", fatal_script_content)

    with pytest.raises(BashScriptError) as excinfo:
        source_and_get_vars(script_path)

    # Check that the exception object contains useful info
    assert excinfo.value.exit_code != 0
    assert "syntax error" in excinfo.value.stderr.lower()


# In tests/test_sentry.py, replace the entire test function with this one.


def test_raises_bash_executable_not_found(monkeypatch, create_script):
    """
    Tests that we raise BashExecutableNotFoundError if 'bash' cannot be found.
    We use monkeypatch to simulate 'bash' not being on the system.
    """
    dummy_script_path = create_script("dummy.sh", "VAR=1").resolve()

    # Create a targeted mock that only affects the fallback paths
    original_is_file = Path.is_file

    def mock_is_file(self):
        # Allow the check for our real test script to pass
        if self == dummy_script_path:
            return original_is_file(self)
        # Fail the check for any other path (i.e., the bash fallbacks)
        return False

    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    monkeypatch.setattr(Path, "is_file", mock_is_file)

    with pytest.raises(BashExecutableNotFoundError):
        source_and_get_vars(dummy_script_path)


def test_empty_script_returns_no_user_vars(create_script):
    """Tests that a valid but empty script returns a dictionary without user-defined vars."""
    script_path = create_script("empty.sh", "#!/bin/bash\n# No variables here")
    variables = source_and_get_vars(script_path)

    # The result will contain some default Bash variables like BASH_VERSINFO.
    # We just need to ensure none of our expected test vars are in there.
    assert "SIMPLE_STRING" not in variables
    assert "FRUITS" not in variables
