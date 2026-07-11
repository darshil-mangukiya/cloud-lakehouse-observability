from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def generate_access_policy(project_root: Path) -> dict[str, Any]:
    classification = json.loads((project_root / "security/data_classification.json").read_text(encoding="utf-8"))
    rows = []
    for dataset_name, policy in sorted(classification.items()):
        rows.append(
            {
                "dataset_name": dataset_name,
                "classification": policy["classification"],
                "pii_columns": ", ".join(policy.get("pii_columns", [])),
                "sensitive_columns": ", ".join(policy.get("sensitive_columns", [])),
                "retention_policy": policy["retention_policy"],
                "access_policy": policy["access_policy"],
                "recommended_control": recommended_control(policy["classification"]),
            }
        )

    output_dir = project_root / "security"
    csv_path = output_dir / "access_policy_matrix.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        "# Access Policy Matrix",
        "",
        f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "| Dataset | Classification | PII Columns | Sensitive Columns | Access Policy | Recommended Control |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        markdown.append(
            f"| {row['dataset_name']} | {row['classification']} | {row['pii_columns']} | "
            f"{row['sensitive_columns']} | {row['access_policy']} | {row['recommended_control']} |"
        )
    markdown_path = output_dir / "access_policy_matrix.md"
    markdown_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(rows),
        "csv_path": str(csv_path.relative_to(project_root)),
        "markdown_path": str(markdown_path.relative_to(project_root)),
    }


def recommended_control(classification: str) -> str:
    if classification == "restricted":
        return "row/column access policy, approval workflow, audit logging"
    if classification == "confidential":
        return "role-based access, encryption, usage monitoring"
    return "standard internal access"
