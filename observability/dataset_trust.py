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


def score_band(score: float) -> str:
    if score >= 90:
        return "Trusted"
    if score >= 75:
        return "Monitor"
    if score >= 60:
        return "At Risk"
    return "Blocked"


def recommended_action(band: str, reason_codes: list[str]) -> str:
    if band == "Trusted":
        return "Publish as certified reporting input and monitor normal SLOs."
    if "critical_open_alert" in reason_codes:
        return "Block publication until critical alerts are resolved and the release gate is re-run."
    if "row_count_anomaly" in reason_codes:
        return "Review source load logs and partition completeness before BI refresh."
    if "failed_quality_gate" in reason_codes:
        return "Resolve failed validation checks and regenerate the affected gold dataset."
    return "Publish only with owner review, exception approval, and monitoring notes."


def dataset_names(items: list[Any]) -> set[str]:
    names = set()
    for item in items:
        if isinstance(item, dict):
            name = item.get("name")
            if name:
                names.add(str(name))
        else:
            names.add(str(item))
    return names


def lineage_score(dataset_name: str, events: list[dict[str, Any]]) -> int:
    for event in events:
        outputs = dataset_names(event.get("outputs", []))
        inputs = dataset_names(event.get("inputs", []))
        if dataset_name in outputs or dataset_name in inputs:
            return 100
        if f"gold.{dataset_name}" in outputs or f"gold.{dataset_name}" in inputs:
            return 100
    return 40


def documentation_score(dataset_name: str, catalog: list[dict[str, Any]]) -> int:
    for entry in catalog:
        if entry.get("dataset_name") == dataset_name and entry.get("owner") and entry.get("business_description"):
            return 100
    return 50


def alert_score(dataset_name: str, alerts: list[dict[str, Any]]) -> tuple[int, list[str]]:
    related = [
        alert
        for alert in alerts
        if alert.get("resolution_status") == "open"
        and (alert.get("dataset_name") == dataset_name or dataset_name in str(alert.get("business_impact", "")))
    ]
    if any(alert.get("severity") == "critical" for alert in related):
        return 30, ["critical_open_alert"]
    if any(alert.get("severity") == "high" for alert in related):
        return 60, ["high_open_alert"]
    if related:
        return 80, ["open_alert"]
    return 100, []


def build_dataset_trust_scores(project_root: Path) -> dict[str, Any]:
    readiness = read_json(project_root / "observability/reports/dataset_readiness.json", [])
    slo_report = read_json(project_root / "observability/reports/slo_report.json", {"gold_slos": []})
    anomalies = read_json(project_root / "observability/reports/row_count_anomalies.json", [])
    catalog = read_json(project_root / "metadata/data_catalog.json", [])
    alerts = read_jsonl(project_root / "alerts/alert_log.jsonl")
    lineage_events = read_jsonl(project_root / "lineage/events.jsonl")

    slo_by_dataset = {row["dataset_name"]: row for row in slo_report.get("gold_slos", [])}
    anomaly_by_dataset = {row["dataset_name"]: row for row in anomalies}
    datasets = []

    for record in readiness:
        dataset_name = record["dataset_name"]
        reason_codes: list[str] = []
        readiness_component = round(float(record.get("readiness_score", 0)) * 100, 2)
        quality_component = 100 if record.get("quality_status") == "passed" else 25
        freshness_component = 100 if record.get("freshness_status") == "passed" else 40
        schema_component = 100 if record.get("schema_status") in {"unchanged", "new_schema", "compatible_evolution"} else 35
        slo_component = 100 if slo_by_dataset.get(dataset_name, {}).get("slo_status") == "passed" else 55
        anomaly_component = 100 if anomaly_by_dataset.get(dataset_name, {}).get("status", "passed") == "passed" else 45
        lineage_component = lineage_score(dataset_name, lineage_events)
        documentation_component = documentation_score(dataset_name, catalog)
        incident_component, alert_reasons = alert_score(dataset_name, alerts)
        reason_codes.extend(alert_reasons)

        if quality_component < 100:
            reason_codes.append("failed_quality_gate")
        if freshness_component < 100 or slo_component < 100:
            reason_codes.append("freshness_or_slo_risk")
        if schema_component < 100:
            reason_codes.append("schema_instability")
        if anomaly_component < 100:
            reason_codes.append("row_count_anomaly")
        if lineage_component < 100:
            reason_codes.append("lineage_incomplete")
        if documentation_component < 100:
            reason_codes.append("documentation_incomplete")

        components = [
            {"name": "readiness", "score": readiness_component, "weight": 0.18},
            {"name": "quality", "score": quality_component, "weight": 0.16},
            {"name": "freshness", "score": freshness_component, "weight": 0.12},
            {"name": "schema_stability", "score": schema_component, "weight": 0.12},
            {"name": "slo_compliance", "score": slo_component, "weight": 0.12},
            {"name": "volume_anomaly", "score": anomaly_component, "weight": 0.10},
            {"name": "lineage_completeness", "score": lineage_component, "weight": 0.08},
            {"name": "documentation_completeness", "score": documentation_component, "weight": 0.06},
            {"name": "incident_history", "score": incident_component, "weight": 0.06},
        ]
        trust_score = round(sum(component["score"] * component["weight"] for component in components), 2)
        band = score_band(trust_score)
        datasets.append(
            {
                "dataset_name": dataset_name,
                "trust_score_overall": trust_score,
                "trust_score_band": band,
                "score_components": components,
                "reason_codes": sorted(set(reason_codes)),
                "recommended_action": recommended_action(band, sorted(set(reason_codes))),
            }
        )

    report = {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(datasets),
        "trusted_count": sum(1 for dataset in datasets if dataset["trust_score_band"] == "Trusted"),
        "monitor_count": sum(1 for dataset in datasets if dataset["trust_score_band"] == "Monitor"),
        "at_risk_count": sum(1 for dataset in datasets if dataset["trust_score_band"] == "At Risk"),
        "blocked_count": sum(1 for dataset in datasets if dataset["trust_score_band"] == "Blocked"),
        "datasets": datasets,
    }
    output_dir = project_root / "observability/reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dataset_trust_scores.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "dataset_trust_scores.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Dataset Trust Scores",
        "",
        f"Scored at: `{report['scored_at']}`",
        "",
        "| Dataset | Score | Band | Reason Codes | Recommended Action |",
        "|---|---:|---|---|---|",
    ]
    for dataset in report["datasets"]:
        reason_codes = ", ".join(dataset["reason_codes"]) if dataset["reason_codes"] else "none"
        lines.append(
            f"| {dataset['dataset_name']} | {dataset['trust_score_overall']} | "
            f"{dataset['trust_score_band']} | {reason_codes} | {dataset['recommended_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
