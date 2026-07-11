from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCENARIOS = [
    {
        "scenario_id": "SCN-001",
        "name": "Breaking ecommerce schema change",
        "trigger": "transaction_id removed without an approved alias",
        "expected_detection": ["source_contract_violation", "schema_drift", "release_gate"],
        "impacted_assets": ["silver_ecommerce_transactions", "gold_revenue_analytics", "gold_customer_analytics"],
        "recommended_response": "Quarantine file, update contract or source mapper, rerun ingestion.",
    },
    {
        "scenario_id": "SCN-002",
        "name": "Null explosion in customer identifier",
        "trigger": "customer_id null rate exceeds quality threshold",
        "expected_detection": ["quality_failure", "gold_dataset_not_ready", "release_gate"],
        "impacted_assets": ["gold_customer_analytics", "gold_data_quality_summary"],
        "recommended_response": "Open source incident with ecommerce team and keep customer mart uncertified.",
    },
    {
        "scenario_id": "SCN-003",
        "name": "Late operational logs",
        "trigger": "operational_logs misses hourly freshness SLO",
        "expected_detection": ["slo_gate", "gold_operational_metrics", "platform_reliability_certification"],
        "impacted_assets": ["gold_operational_metrics", "gold_source_freshness"],
        "recommended_response": "Escalate to data-platform owner and publish with exception only if approved.",
    },
    {
        "scenario_id": "SCN-004",
        "name": "Unexpected PII in gold export",
        "trigger": "new email column appears in gold_customer_analytics",
        "expected_detection": ["pii_classification_gate", "release_gate"],
        "impacted_assets": ["gold_customer_analytics"],
        "recommended_response": "Block release, remove or tokenize column, update classification only after approval.",
    },
    {
        "scenario_id": "SCN-005",
        "name": "Revenue reconciliation mismatch",
        "trigger": "gold revenue total diverges from completed silver transactions",
        "expected_detection": ["reconciliation_gate", "release_gate"],
        "impacted_assets": ["gold_revenue_analytics", "gold_target_vs_actual"],
        "recommended_response": "Compare transformation logic and source filters before finance publication.",
    },
]


def generate_scenario_catalog(project_root: Path) -> dict[str, Any]:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(SCENARIOS),
        "scenarios": SCENARIOS,
    }
    output_dir = project_root / "operations/scenarios"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scenario_catalog.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "scenario_catalog.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Scenario Catalog",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "| Scenario | Trigger | Expected Detection | Impacted Assets | Response |",
        "|---|---|---|---|---|",
    ]
    for scenario in report["scenarios"]:
        lines.append(
            f"| {scenario['scenario_id']} {scenario['name']} | {scenario['trigger']} | "
            f"{', '.join(scenario['expected_detection'])} | {', '.join(scenario['impacted_assets'])} | "
            f"{scenario['recommended_response']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
