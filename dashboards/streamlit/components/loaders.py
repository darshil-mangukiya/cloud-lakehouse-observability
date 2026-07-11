from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


MISSING_ARTIFACT_MESSAGE = "Run make validate-platform to generate this artifact."

GOLD_MARTS: dict[str, dict[str, str]] = {
    "gold_customer_analytics": {
        "business_purpose": "Customer revenue, engagement, support, and retention signals",
        "grain": "one row per customer",
        "key_metrics": "order count, gross revenue, refund count, behavior events, support tickets",
    },
    "gold_revenue_analytics": {
        "business_purpose": "Daily revenue and target attainment",
        "grain": "one row per order date",
        "key_metrics": "completed orders, gross revenue, refunds, failed orders, revenue attainment",
    },
    "gold_marketing_attribution": {
        "business_purpose": "Campaign spend and attributed revenue",
        "grain": "one row per campaign/channel",
        "key_metrics": "spend, attributed orders, attributed revenue, ROAS",
    },
    "gold_product_performance": {
        "business_purpose": "Product and category sales performance",
        "grain": "one row per product",
        "key_metrics": "order count, units sold, gross revenue",
    },
    "gold_operational_metrics": {
        "business_purpose": "Platform health and service runtime signals",
        "grain": "one row per service",
        "key_metrics": "event count, failure count, warning count, average runtime",
    },
    "gold_target_vs_actual": {
        "business_purpose": "Actual revenue/orders versus planning targets",
        "grain": "one row per target date",
        "key_metrics": "actual revenue, target revenue, actual orders, target orders, attainment",
    },
    "gold_data_quality_summary": {
        "business_purpose": "Dataset quality posture",
        "grain": "one row per validated silver dataset",
        "key_metrics": "row count, check count, failed check count, quality status",
    },
    "gold_source_freshness": {
        "business_purpose": "Source load recency and schema version posture",
        "grain": "one row per source/layer load",
        "key_metrics": "row count, schema version, freshness status",
    },
    "fact_orders": {
        "business_purpose": "Order-level fact view for dimensional analysis",
        "grain": "one row per order/transaction",
        "key_metrics": "quantity, amount, completed revenue",
    },
    "fact_marketing_spend": {
        "business_purpose": "Campaign spend fact view",
        "grain": "one row per campaign/date",
        "key_metrics": "spend, impressions, clicks",
    },
    "dim_customer": {
        "business_purpose": "Customer dimension derived from customer analytics",
        "grain": "one row per customer",
        "key_metrics": "customer segment, order count, support tickets, behavior events",
    },
    "dim_product": {
        "business_purpose": "Product dimension derived from standardized product catalog",
        "grain": "one row per product",
        "key_metrics": "product name, category, active flag, list price",
    },
}


def find_project_root(start: Path | None = None) -> Path:
    cursor = (start or Path(__file__)).resolve()
    for path in [cursor, *cursor.parents]:
        if (path / "README.md").exists() and (path / "pipelines").exists() and (path / "dbt").exists():
            return path
    raise RuntimeError("Could not locate project root from dashboard files.")


PROJECT_ROOT = find_project_root()


def artifact_path(relative_path: str | Path) -> Path:
    return PROJECT_ROOT / relative_path


def empty_frame(columns: list[str] | tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return value


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame.map(_coerce_json_value)


def read_csv_artifact(relative_path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    path = artifact_path(relative_path)
    if not path.exists():
        return empty_frame(columns or [])
    try:
        return pd.read_csv(path)
    except (
        FileNotFoundError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
        OSError,
        ValueError,
    ):
        return empty_frame(columns or [])


def read_json_artifact(relative_path: str | Path, default: Any) -> Any:
    path = artifact_path(relative_path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def read_jsonl_artifact(relative_path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    path = artifact_path(relative_path)
    if not path.exists():
        return empty_frame(columns or [])
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"raw_line": line})
    if not rows:
        return empty_frame(columns or [])
    return _normalize_frame(pd.DataFrame(rows))


def read_markdown_artifact(relative_path: str | Path) -> str:
    path = artifact_path(relative_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def artifact_exists(relative_path: str | Path) -> bool:
    return artifact_path(relative_path).exists()


def latest_artifact_timestamp() -> str:
    candidates = [
        "observability/reports/pipeline_run_summary.json",
        "operations/release/release_gate_report.json",
        "observability/reports/dataset_readiness.json",
        "alerts/alert_log.jsonl",
        "metadata/schema_registry.json",
        "lineage/lineage_graph.json",
    ]
    existing = [artifact_path(item) for item in candidates if artifact_path(item).exists()]
    if not existing:
        return "Artifacts not generated"
    latest = max(path.stat().st_mtime for path in existing)
    return datetime.fromtimestamp(latest, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_pipeline_summary() -> dict[str, Any]:
    return read_json_artifact("observability/reports/pipeline_run_summary.json", {})


def load_readiness() -> pd.DataFrame:
    payload = read_json_artifact("observability/reports/dataset_readiness.json", [])
    columns = [
        "dataset_name",
        "evaluated_at",
        "row_count",
        "quality_status",
        "freshness_status",
        "schema_status",
        "readiness_score",
        "readiness_status",
    ]
    return _normalize_frame(pd.DataFrame(payload)) if payload else empty_frame(columns)


def load_trust_scores() -> pd.DataFrame:
    payload = read_json_artifact("observability/reports/dataset_trust_scores.json", {"datasets": []})
    columns = ["dataset_name", "trust_score_overall", "trust_score_band", "reason_codes", "recommended_action"]
    datasets = payload.get("datasets", []) if isinstance(payload, dict) else []
    return _normalize_frame(pd.DataFrame(datasets)) if datasets else empty_frame(columns)


def load_source_freshness() -> pd.DataFrame:
    return read_csv_artifact(
        "gold_layer/gold_source_freshness.csv",
        ["source_system", "layer", "last_load_time", "row_count", "schema_version", "freshness_status"],
    )


def load_quality_summary() -> pd.DataFrame:
    frame = read_csv_artifact(
        "gold_layer/gold_data_quality_summary.csv",
        ["dataset_name", "validated_at", "row_count", "check_count", "failed_check_count", "quality_status"],
    )
    if not frame.empty:
        return frame
    summaries, _ = load_quality_reports()
    return summaries


def load_quality_reports() -> tuple[pd.DataFrame, pd.DataFrame]:
    report_dir = artifact_path("data_quality/reports")
    summary_rows: list[dict[str, Any]] = []
    check_rows: list[dict[str, Any]] = []
    if not report_dir.exists():
        return (
            empty_frame(["dataset_name", "validated_at", "row_count", "check_count", "failed_check_count", "status"]),
            empty_frame(["dataset_name", "check_name", "status", "severity", "observed_value", "threshold", "failed_records"]),
        )
    for path in sorted(report_dir.glob("*_quality_report.json")):
        report = read_json_artifact(path.relative_to(PROJECT_ROOT), {})
        if not report:
            continue
        summary_rows.append(
            {
                "dataset_name": report.get("dataset_name"),
                "validated_at": report.get("validated_at"),
                "row_count": report.get("row_count", 0),
                "check_count": report.get("check_count", 0),
                "failed_check_count": report.get("failed_check_count", 0),
                "status": report.get("status"),
            }
        )
        for result in report.get("results", []):
            check_rows.append({"dataset_name": report.get("dataset_name"), **result})
    return _normalize_frame(pd.DataFrame(summary_rows)), _normalize_frame(pd.DataFrame(check_rows))


def load_rejected_records() -> pd.DataFrame:
    rejected_dir = artifact_path("data_quality/reports/failed_records")
    rows: list[dict[str, Any]] = []
    if not rejected_dir.exists():
        return empty_frame(["source_file", "_reject_reason"])
    for path in sorted(rejected_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                row = {"raw_line": line}
            row["source_file"] = path.name
            rows.append(row)
    return _normalize_frame(pd.DataFrame(rows)) if rows else empty_frame(["source_file", "_reject_reason"])


def load_row_count_anomalies() -> pd.DataFrame:
    payload = read_json_artifact("observability/reports/row_count_anomalies.json", [])
    columns = ["metric", "dataset_name", "status", "row_count", "baseline_row_count", "delta_pct", "threshold"]
    return _normalize_frame(pd.DataFrame(payload)) if payload else empty_frame(columns)


def load_schema_history() -> pd.DataFrame:
    payload = read_json_artifact("metadata/schema_registry.json", {"history": []})
    history = payload.get("history", []) if isinstance(payload, dict) else []
    columns = [
        "source_system",
        "previous_version",
        "current_version",
        "status",
        "added_columns",
        "removed_columns",
        "type_changes",
        "safe_renames",
        "breaking",
        "detected_at",
    ]
    return _normalize_frame(pd.DataFrame(history)) if history else empty_frame(columns)


def load_contract_reports() -> pd.DataFrame:
    report_dir = artifact_path("metadata/contract_reports")
    rows: list[dict[str, Any]] = []
    if not report_dir.exists():
        return empty_frame(["source_system", "dataset_name", "status", "violation_count", "row_count", "validated_at"])
    for path in sorted(report_dir.glob("*/*_contract_report.json")):
        report = read_json_artifact(path.relative_to(PROJECT_ROOT), {})
        if report:
            rows.append(report)
    return _normalize_frame(pd.DataFrame(rows)) if rows else empty_frame(["source_system", "dataset_name", "status", "violation_count", "row_count", "validated_at"])


def load_release_gates() -> tuple[dict[str, Any], pd.DataFrame]:
    payload = read_json_artifact("operations/release/release_gate_report.json", {})
    gates = payload.get("gates", []) if isinstance(payload, dict) else []
    frame = _normalize_frame(pd.DataFrame(gates)) if gates else empty_frame(["gate_name", "status", "severity", "observed", "expected", "recommended_action"])
    return payload, frame


def load_alerts() -> pd.DataFrame:
    return read_jsonl_artifact(
        "alerts/alert_log.jsonl",
        ["alert_id", "timestamp", "severity", "alert_type", "dataset_name", "source_system", "business_impact", "recommended_action", "resolution_status"],
    )


def load_incident_summary() -> str:
    return read_markdown_artifact("observability/reports/incidents/latest_incident_summary.md")


def load_catalog() -> pd.DataFrame:
    payload = read_json_artifact("metadata/data_catalog.json", [])
    columns = [
        "dataset_name",
        "layer",
        "owner",
        "source_system",
        "last_refresh",
        "schema_version",
        "business_description",
        "downstream_usage",
        "refresh_frequency",
        "criticality_tier",
    ]
    if payload:
        return _normalize_frame(pd.DataFrame(payload))
    fallback = [
        {
            "dataset_name": name,
            "layer": "gold" if name.startswith("gold_") else "mart_view",
            "owner": "not generated",
            "source_system": "not generated",
            "last_refresh": "",
            "schema_version": "",
            "business_description": meta["business_purpose"],
            "downstream_usage": "",
            "refresh_frequency": "",
            "criticality_tier": "",
        }
        for name, meta in GOLD_MARTS.items()
    ]
    return pd.DataFrame(fallback, columns=columns)


def load_lineage() -> dict[str, Any]:
    return read_json_artifact("lineage/lineage_graph.json", {"nodes": [], "edges": []})


def load_lineage_edges() -> pd.DataFrame:
    lineage = load_lineage()
    edges = lineage.get("edges", []) if isinstance(lineage, dict) else []
    if not edges:
        return empty_frame(["source", "target", "type"])
    return _normalize_frame(pd.DataFrame(edges))


def load_parquet_manifest() -> dict[str, Any]:
    return read_json_artifact("observability/reports/parquet_export_manifest.json", {"results": [], "written_count": 0, "skipped_count": 0})


def load_gold_dataset(dataset_name: str) -> pd.DataFrame:
    candidates = [
        f"gold_layer/{dataset_name}.csv",
        f"dashboards/exports/{dataset_name}.csv",
        f"sample_outputs/{dataset_name}.csv",
    ]
    for candidate in candidates:
        frame = read_csv_artifact(candidate)
        if not frame.empty:
            return frame
    return empty_frame([])


def load_gold_inventory() -> pd.DataFrame:
    catalog = load_catalog()
    readiness = load_readiness()
    trust = load_trust_scores()
    rows: list[dict[str, Any]] = []
    for dataset_name, meta in GOLD_MARTS.items():
        csv_path = artifact_path(f"gold_layer/{dataset_name}.csv")
        dbt_path = artifact_path(f"dbt/models/marts/{dataset_name}.sql")
        frame = load_gold_dataset(dataset_name)
        catalog_row = catalog[catalog["dataset_name"] == dataset_name] if not catalog.empty and "dataset_name" in catalog else pd.DataFrame()
        readiness_row = readiness[readiness["dataset_name"] == dataset_name] if not readiness.empty and "dataset_name" in readiness else pd.DataFrame()
        trust_row = trust[trust["dataset_name"] == dataset_name] if not trust.empty and "dataset_name" in trust else pd.DataFrame()
        owner = catalog_row.iloc[0].get("owner", "") if not catalog_row.empty else ""
        criticality = catalog_row.iloc[0].get("criticality_tier", "") if not catalog_row.empty else ""
        readiness_status = readiness_row.iloc[0].get("readiness_status", "") if not readiness_row.empty else ""
        trust_score = trust_row.iloc[0].get("trust_score_overall", "") if not trust_row.empty else ""
        last_refresh = datetime.fromtimestamp(csv_path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if csv_path.exists() else ""
        rows.append(
            {
                "dataset_name": dataset_name,
                "row_count": len(frame) if not frame.empty else 0,
                "last_refresh": last_refresh,
                "owner": owner,
                "criticality": criticality,
                "business_purpose": meta["business_purpose"],
                "grain": meta["grain"],
                "key_metrics": meta["key_metrics"],
                "bi_readiness_status": readiness_status or ("model_defined" if dbt_path.exists() else "artifact_missing"),
                "trust_score": trust_score,
                "artifact_status": "csv_available" if csv_path.exists() else ("dbt_model_available" if dbt_path.exists() else "missing"),
            }
        )
    return pd.DataFrame(rows)
