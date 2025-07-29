[![PyPI version](https://badge.fury.io/py/bashvar-sentry.svg)](https://badge.fury.io/py/bashvar-sentry)

Safely source Bash scripts and capture variables in Python.

`bashvar-sentry` provides a secure, sandboxed way to load variables from a Bash script (`.sh` file) into your Python application without the risk of executing arbitrary commands.

## The Problem

Sourcing a shell script to get configuration variables is a common need, but using `subprocess` with `shell=True` is extremely dangerous. A malicious or compromised script could execute any command on your system, like `rm -rf /` or `curl ... | bash`.

## The Solution

`bashvar-sentry` executes the target script in a pseudo sandbox where its `PATH` is empty. This "declaws" the script, preventing it from running any external programs (`ls`, `curl`, `rm`, etc.). It can still define variables using Bash built-ins, which we then safely capture and parse.

### Key Features

* **Secure by Design:** The pseudo sandbox execution prevents shell command injection and other side effects.
* **Full Type Support:** Correctly parses strings, indexed arrays (as Python lists), and associative arrays (as Python dicts).
* **Simple API:** A single function call, `source_and_get_vars()`, is all you need.
* **No Runtime Dependencies:** The core functionality is self-contained.

## Installation

```bash
pip install bashvar-sentry
```

## Quickstart

Let's say you have a configuration file named `config.sh`:

**`config.sh`**

```bash
#!/bin/bash

# This dangerous command will fail safely inside the sandbox
# because 'rm' cannot be found.
rm -rf /tmp/some_important_file

# --- Variables to be sourced ---

# A simple string value
APP_NAME="User Management Service"

# An indexed array of servers
SERVER_LIST=("prod-web-01" "prod-web-02" "prod-db-01")

# An associative array (map) of user roles (requires Bash 4+)
declare -A USER_ROLES
USER_ROLES["admin"]="usr-admin-123"
USER_ROLES["viewer"]="usr-viewer-456"
```

Now, you can safely load these variables in Python.

**`main.py`**

```python
import pprint
from bashvar_sentry import source_and_get_vars, BashScriptError

# --- Example 1: Get all variables from the script ---
print("--- Loading all variables ---")
try:
    all_config = source_and_get_vars("./config.sh")
    pprint.pprint(all_config)
except BashScriptError as e:
    # This might happen if the script has a fatal syntax error
    print(f"Error sourcing script: {e.stderr}")
except FileNotFoundError:
    print("Error: config.sh not found.")

print("\n" + "="*40 + "\n")

# --- Example 2: Get a specific subset of variables ---
print("--- Loading only specific variables ---")
target_keys = ["APP_NAME", "USER_ROLES"]
app_config = source_and_get_vars("./config.sh", target_vars=target_keys)
pprint.pprint(app_config)

```

**Expected Output:**

```
--- Loading all variables ---
{'APP_NAME': 'User Management Service',
 'SERVER_LIST': ['prod-web-01', 'prod-web-02', 'prod-db-01'],
 'USER_ROLES': {'admin': 'usr-admin-123', 'viewer': 'usr-viewer-456'}}

========================================

--- Loading only specific variables ---
{'APP_NAME': 'User Management Service',
 'USER_ROLES': {'admin': 'usr-admin-123', 'viewer': 'usr-viewer-456'}}
```

## API Reference

### `source_and_get_vars(script_path, target_vars=None)`

Safely sources a bash script and returns its variables.

* **`script_path`** (`str | Path`): The absolute or relative path to the bash script to source.
* **`target_vars`** (`Optional[List[str]]`): An optional list of specific variable names to retrieve. If `None` (the default), all variables declared by the script are returned.

**Returns:**

* A `dict` mapping variable names to their values.
  * Bash indexed arrays are converted to Python `list`.
  * Bash associative arrays are converted to Python `dict`.

**Raises:**

* `ScriptNotFoundError`: If the `script_path` does not point to a valid file.
* `BashExecutableNotFoundError`: If the `bash` executable cannot be found on the system.
* `BashScriptError`: If the script itself exits with a fatal syntax error. Non-fatal errors (like a command not found) are ignored.
* `ParsingError`: If the module fails to parse the script's variable output, indicating a very unusual variable declaration.

## License

This project is licensed under the Apache-2.0 License.
