from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def compare_metric(check_name: str, left_value: float, right_value: float, tolerance: float = 0.01) -> dict[str, Any]:
    difference = round(left_value - right_value, 4)
    return {
        "check_name": check_name,
        "left_value": round(left_value, 4),
        "right_value": round(right_value, 4),
        "difference": difference,
        "tolerance": tolerance,
        "status": "passed" if abs(difference) <= tolerance else "failed",
    }


def reconcile_gold_outputs(project_root: Path) -> dict[str, Any]:
    silver_orders = read_csv(project_root / "silver_layer/silver_ecommerce_transactions.csv")
    gold_revenue = read_csv(project_root / "gold_layer/gold_revenue_analytics.csv")
    gold_products = read_csv(project_root / "gold_layer/gold_product_performance.csv")
    gold_targets = read_csv(project_root / "gold_layer/gold_target_vs_actual.csv")

    completed_orders = [row for row in silver_orders if row.get("status") == "completed"]
    silver_completed_revenue = sum(to_float(row.get("amount")) for row in completed_orders)
    silver_completed_order_count = len(completed_orders)
    gold_revenue_total = sum(to_float(row.get("gross_revenue")) for row in gold_revenue)
    gold_completed_orders = sum(to_int(row.get("completed_orders")) for row in gold_revenue)
    gold_product_revenue = sum(to_float(row.get("gross_revenue")) for row in gold_products)
    gold_target_actual_revenue = sum(to_float(row.get("actual_revenue")) for row in gold_targets)

    checks = [
        compare_metric("completed_revenue_silver_to_gold_revenue", silver_completed_revenue, gold_revenue_total),
        compare_metric("completed_order_count_silver_to_gold_revenue", silver_completed_order_count, gold_completed_orders),
        compare_metric("completed_revenue_silver_to_gold_product", silver_completed_revenue, gold_product_revenue),
        compare_metric("gold_revenue_to_target_actual", gold_revenue_total, gold_target_actual_revenue),
    ]
    report = {
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "check_count": len(checks),
        "failed_check_count": sum(1 for check in checks if check["status"] == "failed"),
        "status": "failed" if any(check["status"] == "failed" for check in checks) else "passed",
        "checks": checks,
    }
    output_path = project_root / "data_quality/reports/reconciliation_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
