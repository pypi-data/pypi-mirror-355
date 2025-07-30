# BashVar Sentry

**BashVar Sentry** is a Python utility module that securely extracts Bash variable declarations from scripts by **sourcing** them in a sandboxed environment. It supports sandboxing via `chroot`, `bwrap`, or `fakechroot` to reduce risk from untrusted content.

---

## 📦 Installation

Install from PyPI:

    pip install bashvar-sentry

---

## 🧰 Usage

### As a Python module

```python
from bashvar_sentry import source_and_get_vars

variables = source_and_get_vars(
    "example.sh",
    sandbox_method="auto",           # "auto", "chroot", "bwrap", "fakechroot", "empty"
    jail_dir="/",                    # Optional: target root dir for sandbox
    extra_env={"MYVAR": "from_python"},
    additional_args=["one", "two"]
)

print(variables)
```

---

## 📄 Bash Script Requirements

Your script must be syntactically valid (`bash -n` is run first).

---

### Example Script: `example.sh`

```bash
#!/bin/bash

ARG1=$1
ARG2=$2
ENV_CAPTURED="$MYVAR"

declare -a FRUITS=("apple" "banana split")
declare -A CONFIG=([host]="localhost" [port]="8080")
```

### Output

```python
{
  "ARG1": "one",
  "ARG2": "two",
  "ENV_CAPTURED": "from_python",
  "FRUITS": ["apple", "banana split"],
  "CONFIG": {"host": "localhost", "port": "8080"}
}
```

---

## 🔐 Sandbox Methods

| Method        | Isolation   | Root Required | Notes                      |
|---------------|-------------|---------------|----------------------------|
| `chroot`      | Full        | Yes       | Needs `/usr/sbin/chroot`  |
| `bwrap`       | Strong      | No            | Needs `bwrap` binary       |
| `fakechroot`  | Simulated   | No            | Must have `fakechroot`     |
| `empty`       | Minimal     | No            | Sets `PATH=""`             |
| `auto`        | Best fit    | No            | Picks the first available  |

---

## 🚫 Caveats

- Scripts are **sourced**, not executed. This means:
  - Side effects can persist in the current shell context.
  - Background jobs, subshells, etc., may behave differently.
- Environment is isolated if you use sandboxing. If not, it's up to you.

---

## ✅ Testing

Run tests with:

    python -m pytest

To test sandbox fallbacks, install:

- `/usr/sbin/chroot` and run as root (for chroot) - This auto skips if not root
- `bwrap`
- `fakechroot`

---

## 📄 License

Apache-2.0
