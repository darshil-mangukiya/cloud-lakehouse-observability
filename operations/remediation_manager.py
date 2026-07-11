from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


OWNER_BY_GATE = {
    "silver_quality_gate": "data-governance",
    "critical_alert_gate": "data-platform",
    "slo_gate": "data-platform",
    "data_product_certification_gate": "data-product-owner",
    "semantic_metric_gate": "analytics-engineering",
    "reconciliation_gate": "finance-analytics",
    "pii_classification_gate": "data-governance",
    "catalog_completeness_gate": "data-governance",
    "runtime_gate": "data-platform",
    "lineage_graph_gate": "data-platform",
    "high_alert_gate": "data-platform",
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def priority_for_gate(gate: dict[str, Any]) -> str:
    if gate["severity"] == "critical" and gate["status"] == "failed":
        return "P1"
    if gate["severity"] == "high" and gate["status"] == "failed":
        return "P2"
    if gate["status"] == "warning":
        return "P3"
    return "P4"


def due_at_for_priority(priority: str, now: datetime) -> str:
    hours = {"P1": 4, "P2": 24, "P3": 72, "P4": 168}[priority]
    return (now + timedelta(hours=hours)).isoformat()


def generate_remediation_plan(project_root: Path) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    release = read_json(project_root / "operations/release/release_gate_report.json", {"gates": []})
    certification = read_json(project_root / "operations/certification/data_product_certification_report.json", {"products": []})
    exception_report = read_json(project_root / "operations/exceptions/exception_evaluation_report.json", {"gates": []})
    exception_by_gate = {item["gate_name"]: item for item in exception_report.get("gates", [])}

    tasks = []
    for gate in release.get("gates", []):
        if gate["status"] == "passed":
            continue
        priority = priority_for_gate(gate)
        exception = exception_by_gate.get(gate["gate_name"], {})
        tasks.append(
            {
                "task_id": f"REM-{len(tasks) + 1:03d}",
                "gate_name": gate["gate_name"],
                "priority": priority,
                "owner": OWNER_BY_GATE.get(gate["gate_name"], "data-platform"),
                "due_at": due_at_for_priority(priority, now),
                "exception_applied": exception.get("exception_applied", False),
                "exception_ids": exception.get("exception_ids", []),
                "observed": gate["observed"],
                "expected": gate["expected"],
                "recommended_action": gate["recommended_action"],
                "status": "open",
            }
        )

    for product in certification.get("products", []):
        if product.get("status") != "blocked":
            continue
        for blocker in product.get("blockers", []):
            tasks.append(
                {
                    "task_id": f"REM-{len(tasks) + 1:03d}",
                    "gate_name": "data_product_blocker",
                    "priority": "P1",
                    "owner": product["owner"],
                    "due_at": due_at_for_priority("P1", now),
                    "exception_applied": False,
                    "exception_ids": [],
                    "observed": blocker,
                    "expected": "no blocker",
                    "recommended_action": f"Resolve blocker for {product['name']}: {blocker}",
                    "status": "open",
                }
            )

    report = {
        "generated_at": now.isoformat(),
        "task_count": len(tasks),
        "p1_count": sum(1 for task in tasks if task["priority"] == "P1"),
        "tasks": tasks,
    }
    output_dir = project_root / "operations/remediation"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "remediation_plan.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "remediation_plan.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Remediation Plan",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "| Task | Priority | Owner | Gate | Due | Exception | Action |",
        "|---|---|---|---|---|---|---|",
    ]
    for task in report["tasks"]:
        exception = ", ".join(task["exception_ids"]) if task["exception_ids"] else ""
        lines.append(
            f"| {task['task_id']} | {task['priority']} | {task['owner']} | {task['gate_name']} | "
            f"{task['due_at']} | {exception} | {task['recommended_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
