from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def gate(name: str, status: str, severity: str, observed: Any, expected: Any, action: str) -> dict[str, Any]:
    return {
        "gate_name": name,
        "status": status,
        "severity": severity,
        "observed": observed,
        "expected": expected,
        "recommended_action": action,
    }


def evaluate_release_gate(project_root: Path) -> dict[str, Any]:
    quality_rows = read_jsonl(project_root / "gold_layer/gold_data_quality_summary.jsonl")
    slo_report = read_json(project_root / "observability/reports/slo_report.json", {"failed_slo_count": 0})
    certification = read_json(project_root / "operations/certification/data_product_certification_report.json", {"status": "unknown"})
    semantic = read_json(project_root / "semantic_layer/reports/semantic_validation_report.json", {"status": "unknown"})
    reconciliation = read_json(project_root / "data_quality/reports/reconciliation_report.json", {"status": "unknown"})
    pii = read_json(project_root / "security/pii_scan_report.json", {"status": "unknown"})
    catalog = read_json(project_root / "metadata/catalog_validation_report.json", {"status": "unknown"})
    trust = read_json(project_root / "observability/reports/dataset_trust_scores.json", {"datasets": []})
    runtime = read_json(project_root / "observability/reports/runtime/runtime_profile.json", {"total_duration_seconds": 0})
    lineage_graph = read_json(project_root / "lineage/lineage_graph.json", {"node_count": 0, "edge_count": 0})
    alerts = [alert for alert in read_jsonl(project_root / "alerts/alert_log.jsonl") if alert.get("resolution_status") == "open"]

    failed_quality = [row for row in quality_rows if row.get("quality_status") == "failed"]
    critical_alerts = [alert for alert in alerts if alert.get("severity") == "critical"]
    high_alerts = [alert for alert in alerts if alert.get("severity") == "high"]
    blocked_or_at_risk_trust = [
        dataset
        for dataset in trust.get("datasets", [])
        if dataset.get("trust_score_band") in {"Blocked", "At Risk"}
    ]
    monitor_trust = [
        dataset
        for dataset in trust.get("datasets", [])
        if dataset.get("trust_score_band") == "Monitor"
    ]

    gates = [
        gate(
            "silver_quality_gate",
            "failed" if failed_quality else "passed",
            "critical",
            len(failed_quality),
            0,
            "Resolve failed validation checks or explicitly quarantine affected datasets.",
        ),
        gate(
            "critical_alert_gate",
            "failed" if critical_alerts else "passed",
            "critical",
            len(critical_alerts),
            0,
            "Resolve critical open alerts before certifying a release.",
        ),
        gate(
            "slo_gate",
            "failed" if slo_report.get("failed_slo_count", 0) else "passed",
            "critical",
            slo_report.get("failed_slo_count", 0),
            0,
            "Restore failed SLOs or mark the release as intentionally degraded.",
        ),
        gate(
            "data_product_certification_gate",
            "failed" if certification.get("status") == "blocked" else "passed",
            "critical",
            certification.get("status"),
            "passed",
            "Clear blocked data products or publish with executive exception.",
        ),
        gate(
            "semantic_metric_gate",
            "failed" if semantic.get("status") != "passed" else "passed",
            "high",
            semantic.get("status"),
            "passed",
            "Fix semantic metric references before exposing certified measures.",
        ),
        gate(
            "reconciliation_gate",
            "failed" if reconciliation.get("status") != "passed" else "passed",
            "critical",
            reconciliation.get("status"),
            "passed",
            "Resolve revenue/order reconciliation differences before release.",
        ),
        gate(
            "pii_classification_gate",
            "failed" if pii.get("status") != "passed" else "passed",
            "critical",
            pii.get("status"),
            "passed",
            "Update classification metadata or remove unexpected PII exposure.",
        ),
        gate(
            "catalog_completeness_gate",
            "failed" if catalog.get("status") != "passed" else "passed",
            "high",
            catalog.get("status"),
            "passed",
            "Complete required catalog fields and missing gold entries.",
        ),
        gate(
            "dataset_trust_gate",
            "failed" if blocked_or_at_risk_trust else "warning" if monitor_trust else "passed",
            "critical" if blocked_or_at_risk_trust else "medium",
            {
                "blocked_or_at_risk": [dataset["dataset_name"] for dataset in blocked_or_at_risk_trust],
                "monitor": [dataset["dataset_name"] for dataset in monitor_trust],
            },
            "all gold datasets Trusted or explicitly reviewed",
            "Resolve trust score reason codes or publish with a documented data owner exception.",
        ),
        gate(
            "runtime_gate",
            "warning" if runtime.get("total_duration_seconds", 0) > 60 else "passed",
            "medium",
            runtime.get("total_duration_seconds", 0),
            "<= 60 seconds local smoke run",
            "Investigate slow pipeline phases in runtime profile.",
        ),
        gate(
            "lineage_graph_gate",
            "failed" if lineage_graph.get("node_count", 0) == 0 or lineage_graph.get("edge_count", 0) == 0 else "passed",
            "high",
            {"nodes": lineage_graph.get("node_count", 0), "edges": lineage_graph.get("edge_count", 0)},
            "nodes and edges present",
            "Regenerate lineage events and graph before release.",
        ),
        gate(
            "high_alert_gate",
            "warning" if high_alerts else "passed",
            "medium",
            len(high_alerts),
            0,
            "Review high-severity alerts before release.",
        ),
    ]

    failed_critical = [item for item in gates if item["status"] == "failed" and item["severity"] == "critical"]
    failed_high = [item for item in gates if item["status"] == "failed" and item["severity"] == "high"]
    warnings = [item for item in gates if item["status"] == "warning"]
    if failed_critical or failed_high:
        release_status = "blocked"
        publish_decision = "do_not_publish"
    elif warnings:
        release_status = "conditional"
        publish_decision = "publish_with_exception"
    else:
        release_status = "approved"
        publish_decision = "publish"

    report = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "release_status": release_status,
        "publish_decision": publish_decision,
        "gate_count": len(gates),
        "failed_gate_count": sum(1 for item in gates if item["status"] == "failed"),
        "warning_gate_count": len(warnings),
        "gates": gates,
    }
    output_dir = project_root / "operations/release"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "release_gate_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "release_gate_report.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Release Gate Report",
        "",
        f"Evaluated at: `{report['evaluated_at']}`",
        "",
        f"- Release status: `{report['release_status']}`",
        f"- Publish decision: `{report['publish_decision']}`",
        "",
        "| Gate | Status | Severity | Observed | Expected | Action |",
        "|---|---|---|---|---|---|",
    ]
    for item in report["gates"]:
        lines.append(
            f"| {item['gate_name']} | {item['status']} | {item['severity']} | "
            f"{item['observed']} | {item['expected']} | {item['recommended_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
