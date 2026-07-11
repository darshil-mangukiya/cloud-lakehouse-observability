from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from alerts.alert_manager import AlertManager
from alerts.notification_router import route_alerts
from data_quality.reconciliation import reconcile_gold_outputs
from data_quality.validation_runner import validate_dataset, write_quality_report
from governance.access_policy_generator import generate_access_policy
from governance.pii_scanner import run_pii_scan
from ingestion.contract_validator import validate_contract, write_contract_report
from ingestion.profiler import profile_records
from ingestion.schema_registry import SchemaRegistry, normalize_column_name, read_source_file
from lakehouse.parquet_writer import export_lakehouse_parquet
from lineage.openlineage_emitter import emit_event
from lineage.lineage_graph import generate_lineage_graph
from metadata.audit_manifest import generate_audit_manifest
from metadata.catalog import write_catalog
from metadata.catalog_validator import validate_catalog
from metadata.control_coverage import generate_control_coverage
from observability.cost_monitor import generate_cost_report
from observability.dataset_trust import build_dataset_trust_scores
from observability.metrics_exporter import export_prometheus_metrics
from observability.monitoring import DatasetStateStore, build_readiness_record, row_count_anomaly, write_json
from observability.runtime_profiler import RuntimeProfiler, write_runtime_report
from observability.slo_evaluator import evaluate_slos
from observability.incident_manager import generate_incident_summary
from observability.trust_scorecard import build_trust_scorecard
from operations.backfill_manager import generate_backfill_manifest
from operations.certification_manager import certify_data_products
from operations.exception_manager import evaluate_exceptions
from operations.handoff_generator import generate_final_handoff
from operations.preflight_checker import run_preflight
from operations.release_gate import evaluate_release_gate
from operations.remediation_manager import generate_remediation_plan
from operations.scenario_simulator import generate_scenario_catalog
from operations.sbom_generator import generate_sbom
from semantic_layer.semantic_validator import validate_semantic_layer


DEFAULT_SOURCE_CONFIG = {
    "ecommerce_transactions": {
        "landing_glob": "raw_data/landing/ecommerce_transactions/*",
        "primary_key": "transaction_id",
        "aliases": {"order_id": "transaction_id", "order_value": "amount", "order_timestamp": "order_ts", "user_id": "customer_id"},
    },
    "marketing_campaigns": {
        "landing_glob": "raw_data/landing/marketing_campaigns/*",
        "primary_key": "campaign_id",
        "aliases": {"spend_usd": "spend", "channel_name": "channel"},
    },
    "customer_behavior": {
        "landing_glob": "raw_data/landing/customer_behavior/*",
        "primary_key": "event_id",
        "aliases": {"user_id": "customer_id", "event_time": "event_ts"},
    },
    "product_catalog": {
        "landing_glob": "raw_data/landing/product_catalog/*",
        "primary_key": "product_id",
        "aliases": {},
    },
    "operational_logs": {
        "landing_glob": "raw_data/landing/operational_logs/*",
        "primary_key": "log_id",
        "aliases": {},
    },
    "targets_planning": {
        "landing_glob": "raw_data/landing/targets_planning/*",
        "primary_key": "target_date",
        "aliases": {},
    },
    "crm_support": {
        "landing_glob": "raw_data/landing/crm_support/*",
        "primary_key": "ticket_id",
        "aliases": {"user_id": "customer_id"},
    },
}


def load_source_config(project_root: Path) -> dict[str, dict[str, Any]]:
    config_path = project_root / "config/source_registry.json"
    if not config_path.exists():
        return DEFAULT_SOURCE_CONFIG
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return payload.get("sources", DEFAULT_SOURCE_CONFIG)


SOURCE_CONFIG = load_source_config(PROJECT_ROOT)
SOURCE_GLOBS = {source: config["landing_glob"] for source, config in SOURCE_CONFIG.items()}
SOURCE_PRIMARY_KEYS = {source: config["primary_key"] for source, config in SOURCE_CONFIG.items()}
SOURCE_ALIASES = {source: config.get("aliases", {}) for source, config in SOURCE_CONFIG.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_partition() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def canonicalize(source_system: str, record: dict[str, Any]) -> dict[str, Any]:
    aliases = SOURCE_ALIASES.get(source_system, {})
    canonical: dict[str, Any] = {}
    for raw_key, value in record.items():
        key = normalize_column_name(raw_key)
        key = aliases.get(key, key)
        if isinstance(value, str):
            value = value.strip()
        canonical[key] = value
    return canonical


def dedupe(records: list[dict[str, Any]], primary_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in records:
        key = str(record.get(primary_key, "")).strip()
        if not key:
            rejected.append({**record, "_reject_reason": f"missing primary key {primary_key}"})
            continue
        if key in seen:
            rejected.append({**record, "_reject_reason": f"duplicate primary key {primary_key}"})
            continue
        seen.add(key)
        kept.append(record)
    return kept, rejected


def standardize_ecommerce(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    rejected = []
    for record in records:
        row = canonicalize("ecommerce_transactions", record)
        row["amount"] = round(to_float(row.get("amount")), 2)
        row["quantity"] = to_int(row.get("quantity"), 1)
        row["status"] = str(row.get("status", "")).lower() or "pending"
        row["campaign_id"] = row.get("campaign_id") or "unknown"
        if row["amount"] < 0:
            rejected.append({**row, "_reject_reason": "negative amount"})
            continue
        standardized.append(row)
    clean_records, duplicate_rejects = dedupe(standardized, "transaction_id")
    return clean_records, rejected + duplicate_rejects


def standardize_marketing(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("marketing_campaigns", record)
        row["spend"] = round(to_float(row.get("spend")), 2)
        row["impressions"] = to_int(row.get("impressions"))
        row["clicks"] = to_int(row.get("clicks"))
        row["channel"] = str(row.get("channel", "unknown")).lower()
        standardized.append(row)
    return dedupe(standardized, "campaign_id")


def standardize_behavior(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("customer_behavior", record)
        row["event_type"] = str(row.get("event_type", "unknown")).lower()
        standardized.append(row)
    return dedupe(standardized, "event_id")


def standardize_product(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("product_catalog", record)
        row["active_flag"] = str(row.get("active_flag", "true")).lower() in {"true", "1", "yes", "active"}
        row["list_price"] = round(to_float(row.get("list_price")), 2)
        standardized.append(row)
    return dedupe(standardized, "product_id")


def standardize_ops(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("operational_logs", record)
        row["runtime_seconds"] = to_int(row.get("runtime_seconds"))
        row["status"] = str(row.get("status", "")).lower()
        standardized.append(row)
    return dedupe(standardized, "log_id")


def standardize_targets(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("targets_planning", record)
        row["revenue_target"] = round(to_float(row.get("revenue_target")), 2)
        row["orders_target"] = to_int(row.get("orders_target"))
        standardized.append(row)
    return dedupe(standardized, "target_date")


def standardize_crm(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standardized = []
    for record in records:
        row = canonicalize("crm_support", record)
        row["priority"] = str(row.get("priority", "medium")).lower()
        row["status"] = str(row.get("status", "open")).lower()
        standardized.append(row)
    return dedupe(standardized, "ticket_id")


STANDARDIZERS: dict[str, Callable[[list[dict[str, Any]]], tuple[list[dict[str, Any]], list[dict[str, Any]]]]] = {
    "ecommerce_transactions": standardize_ecommerce,
    "marketing_campaigns": standardize_marketing,
    "customer_behavior": standardize_behavior,
    "product_catalog": standardize_product,
    "operational_logs": standardize_ops,
    "targets_planning": standardize_targets,
    "crm_support": standardize_crm,
}


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for record in records for key in record})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def append_load_log(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "batch_id",
        "source_system",
        "load_time",
        "file_name",
        "row_count",
        "rejected_count",
        "schema_version",
        "load_status",
        "layer",
    ]
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({key: row.get(key) for key in fieldnames})


def clear_runtime_outputs(project_root: Path) -> None:
    for path in [
        project_root / "raw_data/bronze",
        project_root / "silver_layer",
        project_root / "gold_layer",
        project_root / "data_quality/reports",
        project_root / "observability/reports",
        project_root / "dashboards/exports",
        project_root / "metadata/contract_reports",
        project_root / "semantic_layer/reports",
        project_root / "operations/replay",
        project_root / "operations/certification",
        project_root / "operations/release",
        project_root / "operations/remediation",
        project_root / "operations/scenarios",
        project_root / "operations/preflight",
        project_root / "operations/sbom",
        project_root / "metadata/control_coverage",
        project_root / "observability/reports/scorecards",
        project_root / "lakehouse_storage",
        project_root / "parquet_outputs",
        project_root / "spark_outputs",
    ]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    for file_path in [
        project_root / "metadata/load_log.csv",
        project_root / "metadata/schema_registry.json",
        project_root / "observability/run_state.json",
        project_root / "alerts/alert_log.jsonl",
        project_root / "alerts/notification_outbox.jsonl",
        project_root / "lineage/events.jsonl",
        project_root / "lineage/lineage_graph.json",
        project_root / "lineage/lineage_graph.md",
        project_root / "metadata/audit_manifest.json",
        project_root / "metadata/catalog_validation_report.json",
        project_root / "security/pii_scan_report.json",
        project_root / "security/access_policy_matrix.csv",
        project_root / "security/access_policy_matrix.md",
        project_root / "observability/reports/runtime/runtime_profile.json",
    ]:
        if file_path.exists():
            file_path.unlink()


def ingest_sources(project_root: Path, batch_id: str, registry: SchemaRegistry, alerts: AlertManager) -> dict[str, list[dict[str, Any]]]:
    bronze_records: dict[str, list[dict[str, Any]]] = {}
    ingest_date = today_partition()
    load_log = project_root / "metadata/load_log.csv"
    profile_dir = project_root / "metadata/source_profiles"
    contracts_path = project_root / "contracts/source_contracts.json"

    for source_system, glob_pattern in SOURCE_GLOBS.items():
        all_records: list[dict[str, Any]] = []
        files = sorted(project_root.glob(glob_pattern))
        for file_path in files:
            records = read_source_file(file_path)
            contract_report = validate_contract(source_system, records, contracts_path, observed_at=utc_now())
            write_contract_report(
                contract_report,
                project_root / "metadata/contract_reports" / source_system / f"{file_path.stem}_contract_report.json",
            )
            if contract_report["status"] in {"FAIL", "QUARANTINE"}:
                alerts.emit(
                    severity="critical" if contract_report["status"] == "QUARANTINE" else "high",
                    alert_type="source_contract_violation",
                    dataset_name=source_system,
                    source_system=source_system,
                    business_impact=f"Source data returned contract outcome {contract_report['status']} before ingestion completed.",
                    recommended_action="Review contract report, upstream source changes, and downstream gold datasets at risk.",
                )
            drift = registry.register(source_system, records)
            profile = profile_records(records)
            profile_path = profile_dir / source_system / f"{file_path.stem}_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

            if drift.breaking:
                alerts.emit(
                    severity="critical",
                    alert_type="schema_drift",
                    dataset_name=source_system,
                    source_system=source_system,
                    business_impact="Potential dashboard or transformation breakage from source contract violation.",
                    recommended_action=f"Review schema drift report for {file_path.name} and update contract or source mapper.",
                )

            enriched = [
                {
                    **record,
                    "_ingest_batch_id": batch_id,
                    "_source_file": file_path.name,
                    "_source_system": source_system,
                    "_ingested_at": utc_now(),
                    "_schema_version": drift.current_version,
                }
                for record in records
            ]
            all_records.extend(enriched)

            bronze_path = (
                project_root
                / "raw_data/bronze"
                / f"source_system={source_system}"
                / f"ingest_date={ingest_date}"
                / f"batch_id={batch_id}"
                / f"{file_path.stem}.jsonl"
            )
            write_jsonl(bronze_path, enriched)
            append_load_log(
                load_log,
                {
                    "batch_id": batch_id,
                    "source_system": source_system,
                    "load_time": utc_now(),
                    "file_name": file_path.name,
                    "row_count": len(records),
                    "rejected_count": 0,
                    "schema_version": drift.current_version,
                    "load_status": "loaded",
                    "layer": "bronze",
                },
            )
        bronze_records[source_system] = all_records
    return bronze_records


def build_silver(project_root: Path, batch_id: str, bronze_records: dict[str, list[dict[str, Any]]], alerts: AlertManager) -> dict[str, list[dict[str, Any]]]:
    silver: dict[str, list[dict[str, Any]]] = {}
    for source_system, records in bronze_records.items():
        standardizer = STANDARDIZERS[source_system]
        clean_records, rejected = standardizer(records)
        dataset_name = f"silver_{source_system}"
        silver[dataset_name] = clean_records
        write_csv(project_root / "silver_layer" / f"{dataset_name}.csv", clean_records)
        write_jsonl(project_root / "silver_layer" / f"{dataset_name}.jsonl", clean_records)
        if rejected:
            rejected_path = project_root / "data_quality/reports" / "failed_records" / f"{dataset_name}_rejected.jsonl"
            write_jsonl(rejected_path, rejected)
            alerts.emit(
                severity="high",
                alert_type="rejected_records",
                dataset_name=dataset_name,
                source_system=source_system,
                business_impact="Rejected rows reduce reporting completeness and may hide upstream operational issues.",
                recommended_action=f"Inspect {rejected_path.name} and remediate duplicates, missing keys, or invalid values.",
            )
        append_load_log(
            project_root / "metadata/load_log.csv",
            {
                "batch_id": batch_id,
                "source_system": source_system,
                "load_time": utc_now(),
                "file_name": f"{dataset_name}.csv",
                "row_count": len(clean_records),
                "rejected_count": len(rejected),
                "schema_version": "",
                "load_status": "loaded",
                "layer": "silver",
            },
        )
    return silver


def validate_silver(project_root: Path, silver: dict[str, list[dict[str, Any]]], alerts: AlertManager) -> list[dict[str, Any]]:
    reports = []
    for dataset_name, records in silver.items():
        report = validate_dataset(dataset_name, records)
        write_quality_report(report, project_root / "data_quality/reports")
        reports.append(report)
        if report["status"] == "failed":
            alerts.emit(
                severity="critical",
                alert_type="quality_failure",
                dataset_name=dataset_name,
                source_system=dataset_name.replace("silver_", ""),
                business_impact="One or more trusted silver datasets failed quality gates before gold publication.",
                recommended_action="Review Great Expectations report and failed record exports before publishing downstream marts.",
            )
    return reports


def date_from_ts(value: Any) -> str:
    text = str(value or "")
    if "T" in text:
        return text.split("T")[0]
    if " " in text:
        return text.split(" ")[0]
    return text[:10] if len(text) >= 10 else "unknown"


def build_gold(project_root: Path, silver: dict[str, list[dict[str, Any]]], quality_reports: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ecommerce = silver.get("silver_ecommerce_transactions", [])
    products = {row["product_id"]: row for row in silver.get("silver_product_catalog", [])}
    campaigns = {row["campaign_id"]: row for row in silver.get("silver_marketing_campaigns", [])}
    behavior = silver.get("silver_customer_behavior", [])
    support = silver.get("silver_crm_support", [])
    targets = {row["target_date"]: row for row in silver.get("silver_targets_planning", [])}
    ops = silver.get("silver_operational_logs", [])

    customers: dict[str, dict[str, Any]] = {}
    for row in ecommerce:
        customer_id = row.get("customer_id")
        if not customer_id:
            continue
        customer = customers.setdefault(
            customer_id,
            {
                "customer_id": customer_id,
                "order_count": 0,
                "gross_revenue": 0.0,
                "refund_count": 0,
                "last_order_date": "1900-01-01",
                "behavior_events": 0,
                "support_tickets": 0,
            },
        )
        customer["order_count"] += 1
        if row.get("status") == "refunded":
            customer["refund_count"] += 1
        if row.get("status") == "completed":
            customer["gross_revenue"] += to_float(row.get("amount"))
        customer["last_order_date"] = max(customer["last_order_date"], date_from_ts(row.get("order_ts")))
    for row in behavior:
        customer = customers.setdefault(
            row.get("customer_id"),
            {
                "customer_id": row.get("customer_id"),
                "order_count": 0,
                "gross_revenue": 0.0,
                "refund_count": 0,
                "last_order_date": "1900-01-01",
                "behavior_events": 0,
                "support_tickets": 0,
            },
        )
        customer["behavior_events"] += 1
    for row in support:
        customer = customers.setdefault(
            row.get("customer_id"),
            {
                "customer_id": row.get("customer_id"),
                "order_count": 0,
                "gross_revenue": 0.0,
                "refund_count": 0,
                "last_order_date": "1900-01-01",
                "behavior_events": 0,
                "support_tickets": 0,
            },
        )
        customer["support_tickets"] += 1
    gold_customer_analytics = list(customers.values())

    revenue_by_date: dict[str, dict[str, Any]] = {}
    for row in ecommerce:
        order_date = date_from_ts(row.get("order_ts"))
        record = revenue_by_date.setdefault(
            order_date,
            {"order_date": order_date, "completed_orders": 0, "gross_revenue": 0.0, "refund_count": 0, "failed_orders": 0},
        )
        if row.get("status") == "completed":
            record["completed_orders"] += 1
            record["gross_revenue"] += to_float(row.get("amount"))
        elif row.get("status") == "refunded":
            record["refund_count"] += 1
        elif row.get("status") == "failed":
            record["failed_orders"] += 1
    gold_revenue_analytics = []
    for order_date, row in revenue_by_date.items():
        target = targets.get(order_date, {})
        revenue_target = to_float(target.get("revenue_target"))
        row["revenue_target"] = revenue_target
        row["orders_target"] = to_int(target.get("orders_target"))
        row["revenue_attainment"] = round(row["gross_revenue"] / revenue_target, 4) if revenue_target else 0.0
        gold_revenue_analytics.append(row)

    campaign_rollup: dict[str, dict[str, Any]] = {}
    for row in ecommerce:
        campaign_id = row.get("campaign_id") or "unknown"
        campaign = campaigns.get(campaign_id, {})
        record = campaign_rollup.setdefault(
            campaign_id,
            {
                "campaign_id": campaign_id,
                "channel": campaign.get("channel", "unknown"),
                "spend": to_float(campaign.get("spend")),
                "attributed_orders": 0,
                "attributed_revenue": 0.0,
            },
        )
        if row.get("status") == "completed":
            record["attributed_orders"] += 1
            record["attributed_revenue"] += to_float(row.get("amount"))
    for row in campaign_rollup.values():
        row["roas"] = round(row["attributed_revenue"] / row["spend"], 4) if row["spend"] else 0.0
    gold_marketing_attribution = list(campaign_rollup.values())

    product_rollup: dict[str, dict[str, Any]] = {}
    for row in ecommerce:
        product_id = row.get("product_id")
        product = products.get(product_id, {})
        record = product_rollup.setdefault(
            product_id,
            {
                "product_id": product_id,
                "product_name": product.get("product_name", "unknown"),
                "category": product.get("category", "unknown"),
                "active_flag": product.get("active_flag", False),
                "order_count": 0,
                "units_sold": 0,
                "gross_revenue": 0.0,
            },
        )
        if row.get("status") == "completed":
            record["order_count"] += 1
            record["units_sold"] += to_int(row.get("quantity"), 1)
            record["gross_revenue"] += to_float(row.get("amount"))
    gold_product_performance = list(product_rollup.values())

    ops_by_service: dict[str, dict[str, Any]] = {}
    for row in ops:
        service = row.get("service_name", "unknown")
        record = ops_by_service.setdefault(
            service,
            {"service_name": service, "event_count": 0, "failure_count": 0, "warning_count": 0, "avg_runtime_seconds": 0.0, "_runtime_total": 0},
        )
        record["event_count"] += 1
        record["_runtime_total"] += to_int(row.get("runtime_seconds"))
        if row.get("status") == "failed":
            record["failure_count"] += 1
        if row.get("status") == "warning":
            record["warning_count"] += 1
    for row in ops_by_service.values():
        row["avg_runtime_seconds"] = round(row["_runtime_total"] / row["event_count"], 2) if row["event_count"] else 0
        del row["_runtime_total"]
    gold_operational_metrics = list(ops_by_service.values())

    gold_target_vs_actual = [
        {
            "target_date": row["order_date"],
            "actual_revenue": round(row["gross_revenue"], 2),
            "revenue_target": row["revenue_target"],
            "actual_orders": row["completed_orders"],
            "orders_target": row["orders_target"],
            "revenue_attainment": row["revenue_attainment"],
        }
        for row in gold_revenue_analytics
    ]

    gold_data_quality_summary = [
        {
            "dataset_name": report["dataset_name"],
            "validated_at": report["validated_at"],
            "row_count": report["row_count"],
            "check_count": report["check_count"],
            "failed_check_count": report["failed_check_count"],
            "quality_status": report["status"],
        }
        for report in quality_reports
    ]

    load_log_rows = []
    load_log_path = project_root / "metadata/load_log.csv"
    if load_log_path.exists():
        with load_log_path.open(newline="", encoding="utf-8") as handle:
            load_log_rows = list(csv.DictReader(handle))
    gold_source_freshness = [
        {
            "source_system": row["source_system"],
            "layer": row["layer"],
            "last_load_time": row["load_time"],
            "row_count": row["row_count"],
            "schema_version": row["schema_version"],
            "freshness_status": "passed",
        }
        for row in load_log_rows
    ]

    gold = {
        "gold_customer_analytics": gold_customer_analytics,
        "gold_revenue_analytics": gold_revenue_analytics,
        "gold_marketing_attribution": gold_marketing_attribution,
        "gold_product_performance": gold_product_performance,
        "gold_operational_metrics": gold_operational_metrics,
        "gold_target_vs_actual": gold_target_vs_actual,
        "gold_data_quality_summary": gold_data_quality_summary,
        "gold_source_freshness": gold_source_freshness,
    }
    for dataset_name, records in gold.items():
        write_csv(project_root / "gold_layer" / f"{dataset_name}.csv", records)
        write_jsonl(project_root / "gold_layer" / f"{dataset_name}.jsonl", records)
        write_csv(project_root / "dashboards/exports" / f"{dataset_name}.csv", records)
    return gold


def observe(project_root: Path, gold: dict[str, list[dict[str, Any]]], quality_reports: list[dict[str, Any]], alerts: AlertManager) -> list[dict[str, Any]]:
    store = DatasetStateStore(project_root / "observability/run_state.json")
    quality_by_gold = {
        "gold_data_quality_summary": "passed" if all(report["status"] == "passed" for report in quality_reports) else "failed"
    }
    readiness_records = []
    anomalies = []
    for dataset_name, records in gold.items():
        quality_status = quality_by_gold.get(dataset_name, "passed")
        readiness = build_readiness_record(
            dataset_name=dataset_name,
            row_count=len(records),
            quality_status=quality_status,
            freshness_status="passed",
            schema_status="compatible_evolution",
        )
        anomaly = row_count_anomaly(dataset_name, len(records), store)
        anomalies.append(anomaly)
        if anomaly["status"] == "failed":
            alerts.emit(
                severity="high",
                alert_type="row_count_anomaly",
                dataset_name=dataset_name,
                source_system="gold",
                business_impact="Unexpected volume change may indicate missing partitions, duplicated loads, or upstream outages.",
                recommended_action="Compare source load logs and validate partition completeness before publishing dashboards.",
            )
        if readiness["readiness_status"] != "ready":
            alerts.emit(
                severity="critical",
                alert_type="gold_dataset_not_ready",
                dataset_name=dataset_name,
                source_system="gold",
                business_impact="BI consumers may see stale, incomplete, or untrusted data.",
                recommended_action="Resolve failed quality/freshness/schema components and rerun the gold pipeline.",
            )
        readiness_records.append(readiness)
        store.append(dataset_name, {"evaluated_at": utc_now(), "row_count": len(records), "readiness_score": readiness["readiness_score"]})

    write_json(project_root / "observability/reports/dataset_readiness.json", readiness_records)
    write_json(project_root / "observability/reports/row_count_anomalies.json", anomalies)
    export_prometheus_metrics(readiness_records, project_root / "observability/reports/prometheus_metrics.prom")
    write_catalog(
        project_root / "metadata",
        runtime_updates={
            record["dataset_name"]: {
                "last_refresh": record["evaluated_at"],
                "readiness_status": record["readiness_status"],
            }
            for record in readiness_records
        },
    )
    return readiness_records


def run(project_root: Path, reset: bool = False) -> dict[str, Any]:
    if reset:
        clear_runtime_outputs(project_root)
    profiler = RuntimeProfiler()
    batch_id = str(uuid.uuid4())
    registry = SchemaRegistry(project_root / "metadata/schema_registry.json")
    alerts = AlertManager(project_root / "alerts/alert_log.jsonl")
    lineage_path = project_root / "lineage/events.jsonl"

    emit_event(
        lineage_path,
        event_type="START",
        job_name="lakehouse_platform_pipeline",
        batch_id=batch_id,
        inputs=list(SOURCE_GLOBS.keys()),
        outputs=["raw_data/bronze", "silver_layer", "gold_layer"],
        facets={"environment": "local", "orchestrator": "airflow-compatible"},
    )
    preflight_report = run_preflight(project_root)

    step_started = profiler.start_step("bronze_ingestion")
    bronze_records = ingest_sources(project_root, batch_id, registry, alerts)
    profiler.end_step("bronze_ingestion", step_started, {"sources": len(bronze_records)})
    emit_event(
        lineage_path,
        event_type="COMPLETE",
        job_name="bronze_ingestion",
        batch_id=batch_id,
        inputs=list(SOURCE_GLOBS.keys()),
        outputs=[f"bronze.{source}" for source in bronze_records],
        facets={"row_counts": {source: len(records) for source, records in bronze_records.items()}},
    )
    step_started = profiler.start_step("silver_standardization")
    silver = build_silver(project_root, batch_id, bronze_records, alerts)
    profiler.end_step("silver_standardization", step_started, {"datasets": len(silver)})
    emit_event(
        lineage_path,
        event_type="COMPLETE",
        job_name="silver_standardization",
        batch_id=batch_id,
        inputs=[f"bronze.{source}" for source in bronze_records],
        outputs=list(silver.keys()),
        facets={"row_counts": {dataset: len(records) for dataset, records in silver.items()}},
    )
    step_started = profiler.start_step("quality_validation")
    quality_reports = validate_silver(project_root, silver, alerts)
    profiler.end_step("quality_validation", step_started, {"reports": len(quality_reports)})
    step_started = profiler.start_step("gold_publication")
    gold = build_gold(project_root, silver, quality_reports)
    parquet_manifest = export_lakehouse_parquet(
        project_root,
        bronze_records=bronze_records,
        silver=silver,
        gold=gold,
        batch_id=batch_id,
        load_date=today_partition(),
    )
    profiler.end_step(
        "gold_publication",
        step_started,
        {"datasets": len(gold), "parquet_written": parquet_manifest["written_count"], "parquet_skipped": parquet_manifest["skipped_count"]},
    )
    step_started = profiler.start_step("reconciliation")
    reconciliation_report = reconcile_gold_outputs(project_root)
    profiler.end_step("reconciliation", step_started, {"status": reconciliation_report["status"]})
    emit_event(
        lineage_path,
        event_type="COMPLETE",
        job_name="gold_mart_publication",
        batch_id=batch_id,
        inputs=list(silver.keys()),
        outputs=list(gold.keys()),
        facets={"row_counts": {dataset: len(records) for dataset, records in gold.items()}},
    )
    step_started = profiler.start_step("observability_scoring")
    readiness = observe(project_root, gold, quality_reports, alerts)
    slo_report = evaluate_slos(project_root)
    notifications = route_alerts(project_root / "alerts/alert_log.jsonl", project_root / "alerts/notification_outbox.jsonl")
    incident_summary_path = generate_incident_summary(project_root)
    cost_report = generate_cost_report(project_root)
    profiler.end_step(
        "observability_scoring",
        step_started,
        {"ready_gold_datasets": sum(1 for record in readiness if record["readiness_status"] == "ready")},
    )
    step_started = profiler.start_step("governance_validation")
    semantic_report = validate_semantic_layer(project_root)
    access_policy = generate_access_policy(project_root)
    backfill_manifest = generate_backfill_manifest(project_root)
    pii_report = run_pii_scan(project_root)
    catalog_validation = validate_catalog(project_root)
    dataset_trust_report = build_dataset_trust_scores(project_root)
    certification_report = certify_data_products(project_root)
    profiler.end_step(
        "governance_validation",
        step_started,
        {
            "semantic_status": semantic_report["status"],
            "pii_status": pii_report["status"],
            "catalog_status": catalog_validation["status"],
            "trusted_datasets": dataset_trust_report["trusted_count"],
            "certification_status": certification_report["status"],
        },
    )
    runtime_report = write_runtime_report(project_root, profiler)
    lineage_graph = generate_lineage_graph(project_root)
    release_gate_report = evaluate_release_gate(project_root)
    exception_report = evaluate_exceptions(project_root)
    remediation_plan = generate_remediation_plan(project_root)
    trust_scorecard = build_trust_scorecard(project_root)
    emit_event(
        lineage_path,
        event_type="COMPLETE",
        job_name="observability_scoring",
        batch_id=batch_id,
        inputs=list(gold.keys()),
        outputs=[
            "observability.dataset_readiness",
            "observability.slo_report",
            "observability.storage_cost_report",
            "semantic_layer.validation_report",
            "security.access_policy_matrix",
            "security.pii_scan_report",
            "metadata.catalog_validation_report",
            "observability.dataset_trust_scores",
            "operations.backfill_manifest",
            "operations.data_product_certification_report",
            "operations.release_gate_report",
            "operations.exception_evaluation_report",
            "operations.remediation_plan",
            "observability.platform_trust_scorecard",
            "observability.runtime_profile",
            "data_quality.reconciliation_report",
            "alerts.alert_log",
            "metadata.data_catalog",
        ],
        facets={
            "ready_gold_datasets": sum(1 for record in readiness if record["readiness_status"] == "ready"),
            "failed_slo_count": slo_report["failed_slo_count"],
            "notifications_enqueued": len(notifications),
            "incident_summary": str(incident_summary_path.relative_to(project_root)),
            "semantic_validation_status": semantic_report["status"],
            "total_storage_mb": cost_report["total_size_mb"],
            "access_policy_datasets": access_policy["dataset_count"],
            "backfill_candidates": backfill_manifest["candidate_count"],
            "reconciliation_status": reconciliation_report["status"],
            "pii_scan_status": pii_report["status"],
            "catalog_validation_status": catalog_validation["status"],
            "trusted_dataset_count": dataset_trust_report["trusted_count"],
            "certification_status": certification_report["status"],
            "release_status": release_gate_report["release_status"],
            "exception_status": exception_report["status"],
            "remediation_tasks": remediation_plan["task_count"],
            "trust_score": trust_scorecard["trust_score"],
            "pipeline_duration_seconds": runtime_report["total_duration_seconds"],
        },
    )
    emit_event(
        lineage_path,
        event_type="COMPLETE",
        job_name="audit_publication",
        batch_id=batch_id,
        inputs=[
            "lineage/events.jsonl",
            "silver_layer",
            "gold_layer",
            "metadata.data_catalog",
            "observability.reports",
            "security.reports",
        ],
        outputs=["lineage.lineage_graph", "metadata.audit_manifest"],
        facets={"purpose": "artifact integrity and lineage graph publication"},
    )
    lineage_graph = generate_lineage_graph(project_root)
    audit_manifest = generate_audit_manifest(project_root)
    control_coverage = generate_control_coverage(project_root)
    scenario_catalog = generate_scenario_catalog(project_root)
    sbom_report = generate_sbom(project_root)
    audit_manifest = generate_audit_manifest(project_root)

    summary = {
        "batch_id": batch_id,
        "generated_at": utc_now(),
        "bronze_sources": {source: len(records) for source, records in bronze_records.items()},
        "silver_datasets": {dataset: len(records) for dataset, records in silver.items()},
        "gold_datasets": {dataset: len(records) for dataset, records in gold.items()},
        "quality_status": "passed" if all(report["status"] == "passed" for report in quality_reports) else "failed",
        "ready_gold_datasets": sum(1 for record in readiness if record["readiness_status"] == "ready"),
        "alerts_emitted": len(alerts.read_alerts()),
        "failed_slo_count": slo_report["failed_slo_count"],
        "notifications_enqueued": len(notifications),
        "incident_summary": str(incident_summary_path.relative_to(project_root)),
        "semantic_validation_status": semantic_report["status"],
        "reconciliation_status": reconciliation_report["status"],
        "pii_scan_status": pii_report["status"],
        "catalog_validation_status": catalog_validation["status"],
        "trusted_dataset_count": dataset_trust_report["trusted_count"],
        "certification_status": certification_report["status"],
        "release_status": release_gate_report["release_status"],
        "exception_status": exception_report["status"],
        "remediation_tasks": remediation_plan["task_count"],
        "trust_score": trust_scorecard["trust_score"],
        "trust_status": trust_scorecard["trust_status"],
        "estimated_storage_monthly_cost_usd": cost_report["estimated_s3_standard_monthly_cost_usd"],
        "backfill_candidates": backfill_manifest["candidate_count"],
        "audit_artifacts": audit_manifest["artifact_count"],
        "lineage_graph_nodes": lineage_graph["node_count"],
        "pipeline_duration_seconds": runtime_report["total_duration_seconds"],
        "control_coverage_pct": control_coverage["control_coverage_pct"],
        "scenario_count": scenario_catalog["scenario_count"],
        "preflight_status": preflight_report["status"],
        "software_inventory_packages": sbom_report["package_count"],
        "parquet_written_count": parquet_manifest["written_count"],
        "parquet_skipped_count": parquet_manifest["skipped_count"],
    }
    write_json(project_root / "observability/reports/pipeline_run_summary.json", summary)
    handoff_path = generate_final_handoff(project_root)
    summary["handoff_path"] = str(handoff_path.relative_to(project_root))
    write_json(project_root / "observability/reports/pipeline_run_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local lakehouse smoke pipeline.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT), help="Project root path.")
    parser.add_argument("--reset", action="store_true", help="Clear generated runtime outputs before running.")
    args = parser.parse_args()
    summary = run(Path(args.project_root).resolve(), reset=args.reset)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
