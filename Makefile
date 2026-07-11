PROJECT_ROOT := $(shell pwd)
PYTHON ?= python3

.PHONY: help smoke-test run-pipeline unit-test audit local-ci validate-platform dbt-debug dbt-run dbt-test docker-up docker-down dashboard clean

help:
	@echo "Cloud Data Lakehouse & Data Observability Platform"
	@echo "Targets: run-pipeline, smoke-test, unit-test, audit, local-ci, validate-platform, dbt-debug, dbt-run, dbt-test, docker-up, docker-down, dashboard, clean"

run-pipeline:
	$(PYTHON) pipelines/run_platform.py --reset

smoke-test: run-pipeline unit-test

unit-test:
	$(PYTHON) -m unittest discover tests

audit:
	$(PYTHON) scripts/platform_audit.py

local-ci:
	$(PYTHON) scripts/local_ci.py

validate-platform: local-ci

dbt-debug:
	cd dbt && dbt debug --profiles-dir .

dbt-run:
	cd dbt && dbt run --profiles-dir .

dbt-test:
	cd dbt && dbt test --profiles-dir .

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

dashboard:
	streamlit run dashboards/streamlit/app.py

clean:
	rm -rf raw_data/bronze/* silver_layer/* gold_layer/* data_quality/reports/* observability/reports/* dashboards/exports/*
	rm -f metadata/load_log.csv metadata/schema_registry.json observability/run_state.json alerts/alert_log.jsonl
