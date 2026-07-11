from __future__ import annotations

import json
from collections import Counter
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


def generate_incident_summary(project_root: Path) -> Path:
    alerts = read_jsonl(project_root / "alerts/alert_log.jsonl")
    readiness = read_json(project_root / "observability/reports/dataset_readiness.json", [])
    slo_report = read_json(project_root / "observability/reports/slo_report.json", {"failed_slo_count": 0})
    open_alerts = [alert for alert in alerts if alert.get("resolution_status") == "open"]
    severity_counts = Counter(alert["severity"] for alert in open_alerts)
    at_risk = [record for record in readiness if record.get("readiness_status") != "ready"]

    lines = [
        "# Generated Incident Summary",
        "",
        f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Executive Status",
        "",
        f"- Open alerts: `{len(open_alerts)}`",
        f"- Critical alerts: `{severity_counts.get('critical', 0)}`",
        f"- Failed SLOs: `{slo_report.get('failed_slo_count', 0)}`",
        f"- Gold datasets at risk: `{len(at_risk)}`",
        "",
        "## Open Alerts",
        "",
    ]

    if open_alerts:
        lines.append("| Severity | Type | Dataset | Business Impact | Recommended Action |")
        lines.append("|---|---|---|---|---|")
        for alert in open_alerts:
            lines.append(
                f"| {alert['severity']} | {alert['alert_type']} | {alert['dataset_name']} | "
                f"{alert['business_impact']} | {alert['recommended_action']} |"
            )
    else:
        lines.append("No open alerts.")

    lines.extend(["", "## Gold Datasets At Risk", ""])
    if at_risk:
        lines.append("| Dataset | Readiness Score | Quality | Freshness | Schema |")
        lines.append("|---|---:|---|---|---|")
        for record in at_risk:
            lines.append(
                f"| {record['dataset_name']} | {record['readiness_score']} | "
                f"{record['quality_status']} | {record['freshness_status']} | {record['schema_status']} |"
            )
    else:
        lines.append("No gold datasets are currently at risk.")

    lines.extend(
        [
            "",
            "## Operator Next Steps",
            "",
            "1. Triage critical alerts first.",
            "2. Review failed record exports for rejected rows.",
            "3. Check source contract and schema drift reports.",
            "4. Re-run the local CI after remediation.",
        ]
    )

    output_path = project_root / "observability/reports/incidents/latest_incident_summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
