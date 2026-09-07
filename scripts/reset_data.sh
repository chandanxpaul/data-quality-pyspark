#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="$PROJECT_ROOT/data"

if [[ "${1:-}" != "--force" ]]; then
    read -r -p "Remove all generated data under $DATA_ROOT? [y/N] " answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "Reset cancelled."
        exit 0
    fi
fi

for path in input bronze silver gold quarantine dq_metrics; do
    rm -rf -- "$DATA_ROOT/$path"
done

echo "Removed generated data under $DATA_ROOT."
