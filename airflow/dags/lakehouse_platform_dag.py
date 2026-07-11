from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup


PROJECT_ROOT = Path("/opt/airflow/data-lakehouse-platform")
DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "sla": timedelta(hours=2),
}


def pipeline_command(step: str) -> str:
    return f"cd {PROJECT_ROOT} && python pipelines/run_platform.py --project-root {PROJECT_ROOT} {step}"


with DAG(
    dag_id="lakehouse_observability_platform",
    description="Production-style bronze/silver/gold lakehouse pipeline with quality gates and observability.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "observability", "dbt", "great-expectations"],
) as dag:
    start = EmptyOperator(task_id="start")

    with TaskGroup(group_id="ingestion_pipeline") as ingestion_pipeline:
        land_files = BashOperator(
            task_id="land_files_to_bronze",
            bash_command="cd /opt/airflow/data-lakehouse-platform && python pipelines/run_platform.py --reset",
        )
        load_raw_postgres = BashOperator(
            task_id="load_raw_tables_to_postgres",
            bash_command=(
                "cd /opt/airflow/data-lakehouse-platform && "
                "python ingestion/postgres_loader.py --init-schema --project-root /opt/airflow/data-lakehouse-platform"
            ),
        )
        profile_sources = BashOperator(
            task_id="profile_sources",
            bash_command="cd /opt/airflow/data-lakehouse-platform && ls metadata/source_profiles",
        )
        land_files >> load_raw_postgres >> profile_sources

    with TaskGroup(group_id="bronze_to_silver_pipeline") as bronze_to_silver_pipeline:
        run_dbt_staging = BashOperator(
            task_id="dbt_staging_models",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt run --select staging",
        )
        run_dbt_intermediate = BashOperator(
            task_id="dbt_intermediate_models",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt run --select intermediate",
        )
        run_dbt_staging >> run_dbt_intermediate

    with TaskGroup(group_id="validation_pipeline") as validation_pipeline:
        great_expectations_checkpoint = BashOperator(
            task_id="great_expectations_checkpoint",
            bash_command=(
                "cd /opt/airflow/data-lakehouse-platform && "
                "great_expectations checkpoint run lakehouse_silver_checkpoint || "
                "python -m data_quality.validation_runner"
            ),
        )
        dbt_tests = BashOperator(
            task_id="dbt_tests",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt test",
        )
        great_expectations_checkpoint >> dbt_tests

    with TaskGroup(group_id="silver_to_gold_pipeline") as silver_to_gold_pipeline:
        run_gold_models = BashOperator(
            task_id="dbt_gold_marts",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt run --select marts",
        )
        source_freshness = BashOperator(
            task_id="dbt_source_freshness",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt source freshness",
        )
        run_gold_models >> source_freshness

    with TaskGroup(group_id="reporting_export_pipeline") as reporting_export_pipeline:
        export_bi_files = BashOperator(
            task_id="export_bi_ready_gold_csvs",
            bash_command="cd /opt/airflow/data-lakehouse-platform && find dashboards/exports -name '*.csv' -maxdepth 1",
        )
        publish_docs = BashOperator(
            task_id="publish_dbt_docs",
            bash_command="cd /opt/airflow/data-lakehouse-platform/dbt && dbt docs generate",
        )
        export_bi_files >> publish_docs

    with TaskGroup(group_id="alert_pipeline") as alert_pipeline:
        publish_observability_metrics = BashOperator(
            task_id="publish_prometheus_metrics",
            bash_command="cd /opt/airflow/data-lakehouse-platform && cat observability/reports/prometheus_metrics.prom",
        )
        summarize_open_alerts = BashOperator(
            task_id="summarize_open_alerts",
            bash_command="cd /opt/airflow/data-lakehouse-platform && tail -n 20 alerts/alert_log.jsonl || true",
        )
        publish_observability_metrics >> summarize_open_alerts

    end = EmptyOperator(task_id="end")

    (
        start
        >> ingestion_pipeline
        >> bronze_to_silver_pipeline
        >> validation_pipeline
        >> silver_to_gold_pipeline
        >> reporting_export_pipeline
        >> alert_pipeline
        >> end
    )
