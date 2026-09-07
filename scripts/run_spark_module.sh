#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo "Missing .venv. Run 'make setup' first." >&2
    exit 1
fi

if [[ -z "${JAVA_HOME:-}" ]]; then
    if [[ -d "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" ]]; then
        export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
    elif [[ -d "/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" ]]; then
        export JAVA_HOME="/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
    fi
fi

if [[ -n "${JAVA_HOME:-}" ]]; then
    export PATH="$JAVA_HOME/bin:$PATH"
fi

if ! java -version >/dev/null 2>&1; then
    echo "Java 17 was not found. Set JAVA_HOME or install OpenJDK 17." >&2
    exit 1
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <python.module> [stage-name]" >&2
    exit 1
fi

MODULE="$1"
STAGE="${2:-${MODULE##*.}}"

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    BOLD="\033[1m"
    CYAN="\033[36m"
    GREEN="\033[32m"
    RED="\033[31m"
    YELLOW="\033[33m"
    RESET="\033[0m"
else
    BOLD=""
    CYAN=""
    GREEN=""
    RED=""
    YELLOW=""
    RESET=""
fi

log_file="$(mktemp "${TMPDIR:-/tmp}/pyspark-stage.XXXXXX")"
trap 'rm -f "$log_file"' EXIT

printf "\n%b\n" "${BOLD}${CYAN}========== START: ${STAGE} ==========${RESET}"

set +e
"$PROJECT_ROOT/.venv/bin/python" -m "$MODULE" 2>&1 | tee "$log_file"
status=${PIPESTATUS[0]}
set -e

if [[ $status -ne 0 ]]; then
    printf "%b\n" "${BOLD}${RED}========== FAILED: ${STAGE} (exit ${status}) ==========${RESET}" >&2
    exit "$status"
fi

summary="$(tr '\r' '\n' < "$log_file" | grep -E 'Generated [0-9,]+|Appended [0-9,]+|Wrote [0-9,]+|[0-9]+ passed' | tail -n 1 || true)"
if [[ -n "$summary" ]]; then
    printf "%b\n" "${BOLD}${YELLOW}RECORD SUMMARY: ${summary}${RESET}"
else
    printf "%b\n" "${BOLD}${YELLOW}RECORD SUMMARY: no summary emitted by ${STAGE}${RESET}"
fi

printf "%b\n" "${BOLD}${GREEN}========== COMPLETED: ${STAGE} ==========${RESET}"
