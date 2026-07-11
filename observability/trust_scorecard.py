from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def component_score(status: str, pass_value: str = "passed") -> int:
    return 100 if status == pass_value else 0


def build_trust_scorecard(project_root: Path) -> dict[str, Any]:
    readiness = read_json(project_root / "observability/reports/dataset_readiness.json", [])
    slo = read_json(project_root / "observability/reports/slo_report.json", {"failed_slo_count": 0})
    release = read_json(project_root / "operations/release/release_gate_report.json", {"release_status": "unknown"})
    certification = read_json(project_root / "operations/certification/data_product_certification_report.json", {"status": "unknown"})
    dataset_trust = read_json(project_root / "observability/reports/dataset_trust_scores.json", {"datasets": []})
    semantic = read_json(project_root / "semantic_layer/reports/semantic_validation_report.json", {"status": "unknown"})
    reconciliation = read_json(project_root / "data_quality/reports/reconciliation_report.json", {"status": "unknown"})
    pii = read_json(project_root / "security/pii_scan_report.json", {"status": "unknown"})
    catalog = read_json(project_root / "metadata/catalog_validation_report.json", {"status": "unknown"})

    readiness_score = round(
        sum(record.get("readiness_score", 0) for record in readiness) / len(readiness) * 100,
        2,
    ) if readiness else 0
    dataset_trust_score = round(
        sum(record.get("trust_score_overall", 0) for record in dataset_trust.get("datasets", [])) / len(dataset_trust.get("datasets", [])),
        2,
    ) if dataset_trust.get("datasets") else 0
    components = [
        {"name": "dataset_readiness", "score": readiness_score, "weight": 0.18},
        {"name": "dataset_trust", "score": dataset_trust_score, "weight": 0.12},
        {"name": "slo_compliance", "score": 100 if slo.get("failed_slo_count", 0) == 0 else 60, "weight": 0.13},
        {"name": "release_gate", "score": 100 if release.get("release_status") == "approved" else 50 if release.get("release_status") == "conditional" else 25, "weight": 0.13},
        {"name": "data_product_certification", "score": 100 if certification.get("status") == "passed" else 50, "weight": 0.10},
        {"name": "semantic_validation", "score": component_score(semantic.get("status", "")), "weight": 0.10},
        {"name": "reconciliation", "score": component_score(reconciliation.get("status", "")), "weight": 0.09},
        {"name": "pii_classification", "score": component_score(pii.get("status", "")), "weight": 0.075},
        {"name": "catalog_completeness", "score": component_score(catalog.get("status", "")), "weight": 0.075},
    ]
    score = round(sum(item["score"] * item["weight"] for item in components), 2)
    status = "trusted" if score >= 90 else "watch" if score >= 75 else "at_risk"
    report = {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "trust_score": score,
        "trust_status": status,
        "components": components,
    }
    output_dir = project_root / "observability/reports/scorecards"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "platform_trust_scorecard.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "platform_trust_scorecard.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Platform Trust Scorecard",
        "",
        f"Scored at: `{report['scored_at']}`",
        "",
        f"- Trust score: `{report['trust_score']}`",
        f"- Trust status: `{report['trust_status']}`",
        "",
        "| Component | Score | Weight |",
        "|---|---:|---:|",
    ]
    for component in report["components"]:
        lines.append(f"| {component['name']} | {component['score']} | {component['weight']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
