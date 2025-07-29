# src/bashvar_sentry/__init__.py

"""
BashVar Sentry: Safely source bash scripts and extract variables.
"""

__version__ = "1.0.0"

from .exceptions import (
    BashVarSentryError,
    BashScriptError,
    ScriptNotFoundError,
    ParsingError,
    BashExecutableNotFoundError,
)
from .sentry import source_and_get_vars

__all__ = [
    "source_and_get_vars",
    "BashVarSentryError",
    "BashScriptError",
    "ScriptNotFoundError",
    "ParsingError",
    "BashExecutableNotFoundError",
]
