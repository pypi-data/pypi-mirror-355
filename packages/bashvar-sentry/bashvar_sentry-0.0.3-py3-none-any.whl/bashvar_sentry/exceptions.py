# src/bashvar_sentry/exceptions.py


class BashVarSentryError(Exception):
    """Base exception for the bashvar_sentry library."""

    pass


class BashExecutableNotFoundError(BashVarSentryError):
    """Raised when the 'bash' executable cannot be found on the system."""

    pass


class BashScriptError(BashVarSentryError):
    """Raised when the target Bash script fails to execute."""

    def __init__(self, message, stderr, exit_code):
        super().__init__(message)
        self.stderr = stderr
        self.exit_code = exit_code


class ScriptNotFoundError(BashVarSentryError, FileNotFoundError):
    """Raised when the target Bash script does not exist."""

    pass


class ParsingError(BashVarSentryError):
    """Raised when parsing the output of 'declare -p' fails."""

    pass
