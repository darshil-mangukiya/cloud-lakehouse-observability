from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.schema_registry import normalize_column_name, read_source_file


DEFAULT_SOURCE_GLOBS = {
    "ecommerce_transactions": "raw_data/landing/ecommerce_transactions/*",
    "marketing_campaigns": "raw_data/landing/marketing_campaigns/*",
    "customer_behavior": "raw_data/landing/customer_behavior/*",
    "product_catalog": "raw_data/landing/product_catalog/*",
    "operational_logs": "raw_data/landing/operational_logs/*",
    "targets_planning": "raw_data/landing/targets_planning/*",
    "crm_support": "raw_data/landing/crm_support/*",
}

RAW_COLUMNS = {
    "ecommerce_transactions": [
        "transaction_id",
        "order_id",
        "customer_id",
        "product_id",
        "order_ts",
        "order_timestamp",
        "amount",
        "order_value",
        "status",
        "quantity",
        "campaign_id",
        "coupon_code",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "marketing_campaigns": [
        "campaign_id",
        "campaign_date",
        "channel",
        "channel_name",
        "spend",
        "spend_usd",
        "impressions",
        "clicks",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "customer_behavior": [
        "event_id",
        "customer_id",
        "user_id",
        "event_ts",
        "event_time",
        "event_type",
        "product_id",
        "session_id",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "product_catalog": [
        "product_id",
        "product_name",
        "category",
        "active_flag",
        "list_price",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "operational_logs": [
        "log_id",
        "service_name",
        "event_ts",
        "status",
        "runtime_seconds",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "targets_planning": [
        "target_date",
        "revenue_target",
        "orders_target",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
    "crm_support": [
        "ticket_id",
        "customer_id",
        "user_id",
        "created_ts",
        "priority",
        "status",
        "topic",
        "_ingest_batch_id",
        "_source_file",
        "_ingested_at",
    ],
}


def load_source_globs(project_root: Path) -> dict[str, str]:
    config_path = project_root / "config/source_registry.json"
    if not config_path.exists():
        return DEFAULT_SOURCE_GLOBS
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return {source: config["landing_glob"] for source, config in payload.get("sources", {}).items()}


def postgres_dsn() -> str:
    return os.getenv(
        "POSTGRES_DSN",
        "host={host} port={port} dbname={db} user={user} password={password}".format(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            db=os.getenv("POSTGRES_DB", "lakehouse"),
            user=os.getenv("POSTGRES_USER", "lakehouse"),
            password=os.getenv("POSTGRES_PASSWORD", "lakehouse"),
        ),
    )


def get_connection():
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary is required for PostgreSQL loading") from exc
    return psycopg2.connect(postgres_dsn())


def execute_sql_file(cursor, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    cursor.execute(sql)


def init_schema(project_root: Path) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for sql_file in sorted((project_root / "sql/postgres").glob("*.sql")):
                execute_sql_file(cursor, sql_file)


def insert_table_rows(cursor, schema_name: str, table_name: str, columns: list[str], rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    sql = f"insert into {schema_name}.{table_name} ({column_sql}) values ({placeholders})"
    values = [[row.get(column) for column in columns] for row in rows]
    cursor.executemany(sql, values)
    return len(rows)


def insert_rows(cursor, table_name: str, columns: list[str], rows: list[dict[str, Any]]) -> int:
    return insert_table_rows(cursor, "raw", table_name, columns, rows)


def load_raw_sources(project_root: Path) -> dict[str, int]:
    batch_id = str(uuid.uuid4())
    ingested_at = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}
    source_globs = load_source_globs(project_root)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for source_system, glob_pattern in source_globs.items():
                rows = []
                for file_path in sorted(project_root.glob(glob_pattern)):
                    for record in read_source_file(file_path):
                        normalized = {normalize_column_name(key): value for key, value in record.items()}
                        normalized["_ingest_batch_id"] = batch_id
                        normalized["_source_file"] = file_path.name
                        normalized["_ingested_at"] = ingested_at
                        rows.append(normalized)
                cursor.execute(f"truncate table raw.{source_system}")
                counts[source_system] = insert_rows(cursor, source_system, RAW_COLUMNS[source_system], rows)
    return counts


def load_control_tables(project_root: Path) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            quality_path = project_root / "gold_layer/gold_data_quality_summary.csv"
            if quality_path.exists():
                cursor.execute("truncate table raw.data_quality_summary")
                with quality_path.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                insert_rows(
                    cursor,
                    "data_quality_summary",
                    ["dataset_name", "validated_at", "row_count", "check_count", "failed_check_count", "quality_status"],
                    rows,
                )
            load_log_path = project_root / "metadata/load_log.csv"
            if load_log_path.exists():
                cursor.execute("truncate table raw.load_log")
                with load_log_path.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                for row in rows:
                    if row.get("schema_version") == "":
                        row["schema_version"] = None
                insert_rows(
                    cursor,
                    "load_log",
                    ["source_system", "layer", "load_time", "row_count", "schema_version"],
                    rows,
                )
            load_contract_validation_results(cursor, project_root)
            load_dataset_trust_scores(cursor, project_root)


def load_contract_validation_results(cursor, project_root: Path) -> None:
    report_paths = sorted((project_root / "metadata/contract_reports").glob("*/*_contract_report.json"))
    if not report_paths:
        return
    cursor.execute("truncate table metadata.source_contract_validation")
    rows = []
    for report_path in report_paths:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "source_system": report["source_system"],
                "dataset_name": report.get("dataset_name", report["source_system"]),
                "validated_at": report["validated_at"],
                "observed_at": report.get("observed_at"),
                "owner": report["owner"],
                "business_domain": report.get("business_domain"),
                "business_criticality": report.get("business_criticality"),
                "criticality_tier": report["criticality_tier"],
                "schema_compatibility_mode": report.get("schema_compatibility_mode"),
                "status": report["status"],
                "outcome": report.get("outcome", report["status"]),
                "row_count": report.get("row_count", 0),
                "violation_count": report.get("violation_count", len(report.get("violations", []))),
                "observed_columns": json.dumps(report.get("observed_columns", [])),
                "expected_columns": json.dumps(report.get("expected_columns", [])),
                "safe_renames_applied": json.dumps(report.get("safe_renames_applied", {})),
                "violations": json.dumps(report.get("violations", [])),
                "downstream_dependencies": json.dumps(report.get("downstream_dependencies", [])),
            }
        )
    insert_table_rows(
        cursor,
        "metadata",
        "source_contract_validation",
        [
            "source_system",
            "dataset_name",
            "validated_at",
            "observed_at",
            "owner",
            "business_domain",
            "business_criticality",
            "criticality_tier",
            "schema_compatibility_mode",
            "status",
            "outcome",
            "row_count",
            "violation_count",
            "observed_columns",
            "expected_columns",
            "safe_renames_applied",
            "violations",
            "downstream_dependencies",
        ],
        rows,
    )


def load_dataset_trust_scores(cursor, project_root: Path) -> None:
    trust_path = project_root / "observability/reports/dataset_trust_scores.json"
    if not trust_path.exists():
        return
    report = json.loads(trust_path.read_text(encoding="utf-8"))
    cursor.execute("truncate table observability.dataset_trust_scores")
    rows = []
    for dataset in report.get("datasets", []):
        rows.append(
            {
                "dataset_name": dataset["dataset_name"],
                "scored_at": report["scored_at"],
                "trust_score_overall": dataset["trust_score_overall"],
                "trust_score_band": dataset["trust_score_band"],
                "reason_codes": json.dumps(dataset.get("reason_codes", [])),
                "recommended_action": dataset["recommended_action"],
                "score_components": json.dumps(dataset.get("score_components", [])),
            }
        )
    insert_table_rows(
        cursor,
        "observability",
        "dataset_trust_scores",
        [
            "dataset_name",
            "scored_at",
            "trust_score_overall",
            "trust_score_band",
            "reason_codes",
            "recommended_action",
            "score_components",
        ],
        rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Load local lakehouse sources into PostgreSQL raw tables for dbt.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--init-schema", action="store_true")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    if args.init_schema:
        init_schema(project_root)
    counts = load_raw_sources(project_root)
    load_control_tables(project_root)
    print(counts)


if __name__ == "__main__":
    main()
