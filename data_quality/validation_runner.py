from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    check_name: str
    status: str
    severity: str
    observed_value: Any
    threshold: Any
    failed_records: int = 0


QUALITY_SUITES: dict[str, dict[str, Any]] = {
    "silver_ecommerce_transactions": {
        "required_columns": ["transaction_id", "customer_id", "product_id", "order_ts", "amount", "status"],
        "unique_columns": ["transaction_id"],
        "null_thresholds": {"transaction_id": 0.0, "customer_id": 0.01, "amount": 0.02},
        "accepted_values": {"status": ["completed", "refunded", "failed", "pending"]},
        "non_negative": ["amount"],
    },
    "silver_marketing_campaigns": {
        "required_columns": ["campaign_id", "campaign_date", "channel", "spend"],
        "unique_columns": ["campaign_id"],
        "null_thresholds": {"campaign_id": 0.0, "spend": 0.05},
        "non_negative": ["spend"],
    },
    "silver_customer_behavior": {
        "required_columns": ["event_id", "customer_id", "event_ts", "event_type"],
        "unique_columns": ["event_id"],
        "null_thresholds": {"event_id": 0.0, "customer_id": 0.05},
    },
    "silver_product_catalog": {
        "required_columns": ["product_id", "product_name", "category", "active_flag"],
        "unique_columns": ["product_id"],
        "null_thresholds": {"product_id": 0.0, "category": 0.02},
    },
    "silver_operational_logs": {
        "required_columns": ["log_id", "service_name", "event_ts", "status"],
        "unique_columns": ["log_id"],
        "accepted_values": {"status": ["ok", "warning", "failed"]},
    },
    "silver_targets_planning": {
        "required_columns": ["target_date", "revenue_target", "orders_target"],
        "unique_columns": ["target_date"],
        "non_negative": ["revenue_target", "orders_target"],
    },
    "silver_crm_support": {
        "required_columns": ["ticket_id", "customer_id", "created_ts", "priority", "status"],
        "unique_columns": ["ticket_id"],
        "accepted_values": {"priority": ["low", "medium", "high", "urgent"]},
    },
}


def _null_rate(records: list[dict[str, Any]], column: str) -> float:
    if not records:
        return 0.0
    return sum(1 for row in records if row.get(column) in (None, "")) / len(records)


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_dataset(dataset_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    suite = QUALITY_SUITES.get(dataset_name, {})
    results: list[CheckResult] = []
    columns = set(records[0].keys()) if records else set()

    missing_columns = sorted(set(suite.get("required_columns", [])) - columns)
    results.append(
        CheckResult(
            check_name="schema_required_columns",
            status="failed" if missing_columns else "passed",
            severity="critical",
            observed_value=missing_columns,
            threshold=suite.get("required_columns", []),
            failed_records=len(records) if missing_columns else 0,
        )
    )

    for column in suite.get("unique_columns", []):
        values = [row.get(column) for row in records if row.get(column) not in (None, "")]
        counts = Counter(values)
        duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
        results.append(
            CheckResult(
                check_name=f"unique_{column}",
                status="failed" if duplicate_count else "passed",
                severity="critical",
                observed_value=duplicate_count,
                threshold=0,
                failed_records=duplicate_count,
            )
        )

    for column, threshold in suite.get("null_thresholds", {}).items():
        observed = _null_rate(records, column)
        results.append(
            CheckResult(
                check_name=f"null_rate_{column}",
                status="failed" if observed > threshold else "passed",
                severity="high",
                observed_value=round(observed, 4),
                threshold=threshold,
                failed_records=sum(1 for row in records if row.get(column) in (None, "")),
            )
        )

    for column, allowed_values in suite.get("accepted_values", {}).items():
        bad_values = [row.get(column) for row in records if row.get(column) not in allowed_values]
        results.append(
            CheckResult(
                check_name=f"accepted_values_{column}",
                status="failed" if bad_values else "passed",
                severity="medium",
                observed_value=sorted({str(value) for value in bad_values}),
                threshold=allowed_values,
                failed_records=len(bad_values),
            )
        )

    for column in suite.get("non_negative", []):
        bad_values = [row for row in records if (_to_float(row.get(column)) is None or _to_float(row.get(column)) < 0)]
        results.append(
            CheckResult(
                check_name=f"non_negative_{column}",
                status="failed" if bad_values else "passed",
                severity="high",
                observed_value=len(bad_values),
                threshold=">= 0",
                failed_records=len(bad_values),
            )
        )

    failed = [result for result in results if result.status == "failed"]
    return {
        "dataset_name": dataset_name,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(records),
        "check_count": len(results),
        "failed_check_count": len(failed),
        "status": "failed" if failed else "passed",
        "results": [asdict(result) for result in results],
    }


def write_quality_report(report: dict[str, Any], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{report['dataset_name']}_quality_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
