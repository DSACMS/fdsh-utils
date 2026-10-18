#!/bin/sh

set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MOCK_SERVICE_DIR=$(dirname "$SCRIPT_DIR")
LOG_FILE="$SCRIPT_DIR/test_run.log"
WRITE_LOG=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTION]

Run all mock-service tests, including BDD and property-based tests.

Options:
  --log       Write output to test/test_run.log if the test run fails.
  --no-log    Do not write a test log. This is the default.
  -h, --help  Show this help message.
EOF
}

case "${1:-}" in
    "") ;;
    --log) WRITE_LOG=1 ;;
    --no-log) WRITE_LOG=0 ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        printf 'Unknown option: %s\n\n' "$1" >&2
        usage >&2
        exit 2
        ;;
esac

if [ "$#" -gt 1 ]; then
    printf 'Only one option may be supplied.\n\n' >&2
    usage >&2
    exit 2
fi

if [ -x "$MOCK_SERVICE_DIR/venvtest/bin/python" ]; then
    PYTHON="$MOCK_SERVICE_DIR/venvtest/bin/python"
elif [ -x "$MOCK_SERVICE_DIR/.venv/bin/python" ]; then
    PYTHON="$MOCK_SERVICE_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON=$(command -v python3)
elif command -v python >/dev/null 2>&1; then
    PYTHON=$(command -v python)
else
    printf 'No Python interpreter was found.\n' >&2
    exit 127
fi

TEMP_OUTPUT=$(mktemp "${TMPDIR:-/tmp}/mock-service-tests.XXXXXX")
cleanup() {
    rm -f "$TEMP_OUTPUT"
}
trap cleanup EXIT HUP INT TERM

if [ "$WRITE_LOG" -eq 1 ]; then
    rm -f "$LOG_FILE"
fi

printf 'Running mock-service tests with %s\n' "$PYTHON"
(
    cd "$MOCK_SERVICE_DIR" || exit 1
    PYTHONPATH="$MOCK_SERVICE_DIR/auth:$MOCK_SERVICE_DIR/api${PYTHONPATH:+:$PYTHONPATH}" \
        "$PYTHON" -m pytest test -q
) >"$TEMP_OUTPUT" 2>&1
TEST_RESULT=$?

cat "$TEMP_OUTPUT"

if [ "$TEST_RESULT" -ne 0 ] && [ "$WRITE_LOG" -eq 1 ]; then
    cp "$TEMP_OUTPUT" "$LOG_FILE"
    printf '\nFailed test output written to %s\n' "$LOG_FILE" >&2
fi

exit "$TEST_RESULT"
