#!/bin/bash

BASH_PATH="$1"
TARGET_SCRIPT="$2"

if [ -z "$TARGET_SCRIPT" ]; then
  echo "Error: No target script path provided." >&2
  exit 1
fi

if [ ! -f "$TARGET_SCRIPT" ]; then
  echo "Error: Target script not found at '$TARGET_SCRIPT'" >&2
  exit 2
fi

"$BASH_PATH" -n "$TARGET_SCRIPT" || exit $?

#    If the syntax is valid, source the file to get variables.
#    This will still allow non-fatal errors (like 'command not found')
#    to occur without stopping the script.
# shellcheck disable=SC1090
. "$TARGET_SCRIPT"

# 3. Dump the variables.
declare -p
