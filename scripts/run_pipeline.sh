#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ "${1:-}" == "--reset" ]]; then
    "$PROJECT_ROOT/scripts/reset_data.sh" --force
elif [[ $# -ne 0 ]]; then
    echo "Usage: $0 [--reset]" >&2
    exit 1
elif [[ -d "$PROJECT_ROOT/data/bronze/_delta_log" ]]; then
    echo "Bronze data already exists and ingestion uses append mode." >&2
    echo "Run 'make pipeline-reset' to clear generated data before rerunning." >&2
    exit 1
fi

"$PROJECT_ROOT/scripts/run_spark_module.sh" src.generate_mock_data generate
"$PROJECT_ROOT/scripts/run_spark_module.sh" src.bronze_ingestion bronze
"$PROJECT_ROOT/scripts/run_spark_module.sh" src.silver_dq_processing silver
"$PROJECT_ROOT/scripts/run_spark_module.sh" src.gold_aggregation gold
