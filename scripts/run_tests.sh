#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo "Missing .venv. Run 'make setup' first." >&2
    exit 1
fi

exec "$PROJECT_ROOT/scripts/run_spark_module.sh" pytest tests
