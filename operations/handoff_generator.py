from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def generate_final_handoff(project_root: Path) -> Path:
    summary = read_json(project_root / "observability/reports/pipeline_run_summary.json", {})
    release = read_json(project_root / "operations/release/release_gate_report.json", {})
    scorecard = read_json(project_root / "observability/reports/scorecards/platform_trust_scorecard.json", {})
    coverage = read_json(project_root / "metadata/control_coverage/control_coverage_report.json", {})
    certification = read_json(project_root / "operations/certification/data_product_certification_report.json", {})
    remediation = read_json(project_root / "operations/remediation/remediation_plan.json", {})

    lines = [
        "# Final Project Handoff",
        "",
        f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Latest Run",
        "",
        f"- Batch ID: `{summary.get('batch_id', 'unknown')}`",
        f"- Quality status: `{summary.get('quality_status', 'unknown')}`",
        f"- Release status: `{release.get('release_status', 'unknown')}`",
        f"- Publish decision: `{release.get('publish_decision', 'unknown')}`",
        f"- Trust score: `{scorecard.get('trust_score', 'unknown')}`",
        f"- Trust status: `{scorecard.get('trust_status', 'unknown')}`",
        f"- Control coverage: `{coverage.get('control_coverage_pct', 'unknown')}`",
        f"- Certified data products: `{certification.get('certified_count', 0)}`",
        f"- Blocked data products: `{certification.get('blocked_count', 0)}`",
        f"- Remediation tasks: `{remediation.get('task_count', 0)}`",
        "",
        "## What To Review First",
        "",
        "1. `README.md` for project overview and quick start.",
        "2. `PORTFOLIO_OUTPUTS.md` for resume and interview language.",
        "3. `docs/architecture.md` and `docs/lineage.md` for system design.",
        "4. `docs/operator_cli.md` for operating commands.",
        "5. `operations/release/release_gate_report.md` for publish decision.",
        "6. `operations/remediation/remediation_plan.md` for owner-routed next steps.",
        "",
        "## Strong Interview Angles",
        "",
        "- Modern lakehouse layering with bronze, silver, and gold datasets.",
        "- Source contracts, schema drift detection, and safe schema evolution.",
        "- dbt modeling, Great Expectations validation, and BI-ready gold marts.",
        "- Observability, release gates, certification, remediation, and governance controls.",
        "- Local reproducibility with Docker, Make, and dependency-light smoke tests.",
        "",
    ]
    output_path = project_root / "docs/FINAL_PROJECT_HANDOFF.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
