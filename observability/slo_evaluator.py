from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def evaluate_slos(project_root: Path) -> dict[str, Any]:
    contracts = load_json(project_root / "contracts/source_contracts.json")
    readiness = load_json(project_root / "observability/reports/dataset_readiness.json")
    load_log = load_csv(project_root / "metadata/load_log.csv")
    latest_by_source: dict[str, dict[str, str]] = {}
    for row in load_log:
        source = row["source_system"]
        if source not in latest_by_source or row["load_time"] > latest_by_source[source]["load_time"]:
            latest_by_source[source] = row

    source_slos = []
    for source_system, contract in contracts.items():
        latest = latest_by_source.get(source_system)
        source_slos.append(
            {
                "source_system": source_system,
                "owner": contract["owner"],
                "criticality_tier": contract["criticality_tier"],
                "freshness_sla_hours": contract["freshness_sla_hours"],
                "last_load_time": latest["load_time"] if latest else None,
                "loaded": latest is not None,
                "slo_status": "passed" if latest else "failed",
            }
        )

    gold_slos = []
    for record in readiness:
        target = 0.95 if record["dataset_name"] in {
            "gold_customer_analytics",
            "gold_revenue_analytics",
            "gold_operational_metrics",
            "gold_data_quality_summary",
            "gold_source_freshness",
        } else 0.90
        gold_slos.append(
            {
                "dataset_name": record["dataset_name"],
                "readiness_score": record["readiness_score"],
                "readiness_target": target,
                "slo_status": "passed" if record["readiness_score"] >= target else "failed",
            }
        )

    report = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "source_slos": source_slos,
        "gold_slos": gold_slos,
        "failed_slo_count": sum(1 for row in source_slos + gold_slos if row["slo_status"] == "failed"),
    }
    output_path = project_root / "observability/reports/slo_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
