PYTHON := .venv/bin/python

.PHONY: setup generate bronze silver gold pipeline pipeline-reset reset-data test

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

generate:
	./scripts/run_spark_module.sh src.generate_mock_data generate

bronze:
	./scripts/run_spark_module.sh src.bronze_ingestion bronze

silver:
	./scripts/run_spark_module.sh src.silver_dq_processing silver

gold:
	./scripts/run_spark_module.sh src.gold_aggregation gold

pipeline:
	./scripts/run_pipeline.sh

pipeline-reset:
	./scripts/run_pipeline.sh --reset

reset-data:
	./scripts/reset_data.sh

test:
	./scripts/run_tests.sh
