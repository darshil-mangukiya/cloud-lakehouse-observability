from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACTS = [
    "README.md",
    "Makefile",
    "pipelines/run_platform.py",
    "contracts/source_contracts.json",
    "data_quality/validation_runner.py",
    "dbt/dbt_project.yml",
    "airflow/dags/lakehouse_platform_dag.py",
    "docker-compose.yml",
]

OPTIONAL_COMMANDS = ["docker", "dbt", "airflow", "streamlit", "psql"]


def check_artifacts(project_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "name": relative_path,
            "type": "required_artifact",
            "status": "passed" if (project_root / relative_path).exists() else "failed",
            "details": str(project_root / relative_path),
        }
        for relative_path in REQUIRED_ARTIFACTS
    ]


def check_commands() -> list[dict[str, Any]]:
    checks = []
    for command in OPTIONAL_COMMANDS:
        resolved = shutil.which(command)
        checks.append(
            {
                "name": command,
                "type": "optional_command",
                "status": "passed" if resolved else "warning",
                "details": resolved or "not found on PATH",
            }
        )
    return checks


def run_preflight(project_root: Path) -> dict[str, Any]:
    checks = [
        {
            "name": "python_version",
            "type": "runtime",
            "status": "passed" if sys.version_info >= (3, 10) else "failed",
            "details": sys.version.split()[0],
        }
    ]
    checks.extend(check_artifacts(project_root))
    checks.extend(check_commands())

    failed = [check for check in checks if check["status"] == "failed"]
    warnings = [check for check in checks if check["status"] == "warning"]
    status = "failed" if failed else "passed_with_warnings" if warnings else "passed"
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "check_count": len(checks),
        "failed_count": len(failed),
        "warning_count": len(warnings),
        "checks": checks,
    }
    output_dir = project_root / "operations/preflight"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "preflight_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "preflight_report.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Preflight Report",
        "",
        f"Checked at: `{report['checked_at']}`",
        "",
        f"- Status: `{report['status']}`",
        f"- Failed checks: `{report['failed_count']}`",
        f"- Warnings: `{report['warning_count']}`",
        "",
        "| Check | Type | Status | Details |",
        "|---|---|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['type']} | {check['status']} | {check['details']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
