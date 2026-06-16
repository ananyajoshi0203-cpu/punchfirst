#!/bin/bash
#
# punchfirst pre-tool-use hook
#
# Blocks Write/Edit to a production file if no corresponding test file exists.
# Runs automatically via .claude/settings.json before every file write.
#
# Skips: test files themselves, config files, migrations, __init__.py, docs

set -euo pipefail

# The file being written is passed as the first argument by Claude Code
FILE="${1:-}"

if [ -z "$FILE" ]; then
  exit 0
fi

# Normalize path
BASENAME=$(basename "$FILE")
DIRNAME=$(dirname "$FILE")

# Skip: already a test file
if [[ "$BASENAME" == test_* ]] || [[ "$BASENAME" == *_test.py ]]; then
  exit 0
fi

# Skip: non-Python files
if [[ "$FILE" != *.py ]]; then
  exit 0
fi

# Skip: config, migrations, init, setup files
SKIP_PATTERNS=("__init__.py" "conftest.py" "setup.py" "settings.py" "config.py" "migrations")
for pattern in "${SKIP_PATTERNS[@]}"; do
  if [[ "$BASENAME" == "$pattern" ]] || [[ "$FILE" == *"$pattern"* ]]; then
    exit 0
  fi
done

# Derive expected test file name
MODULE_NAME="${BASENAME%.py}"
EXPECTED_TEST="test_${MODULE_NAME}.py"

# Search for the test file in common locations
FOUND=0
for search_dir in "tests" "test" "." "$DIRNAME" "${DIRNAME}/../tests" "${DIRNAME}/../test"; do
  if [ -f "${search_dir}/${EXPECTED_TEST}" ]; then
    FOUND=1
    break
  fi
done

if [ "$FOUND" -eq 0 ]; then
  echo ""
  echo "punchfirst: no test file found for '$BASENAME'"
  echo ""
  echo "  Expected: $EXPECTED_TEST"
  echo "  The test throws the first punch. Write the test before the code."
  echo ""
  echo "  To skip: set PUNCHFIRST_SKIP=1 in your environment"
  echo ""

  # Allow override via env var for legitimate skips (migrations, generated code)
  if [ "${PUNCHFIRST_SKIP:-0}" = "1" ]; then
    echo "  (override active — proceeding)"
    exit 0
  fi

  exit 1
fi

exit 0
