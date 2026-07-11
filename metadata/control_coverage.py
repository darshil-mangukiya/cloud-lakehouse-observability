from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTROL_FILES = {
    "source_contract": "contracts/source_contracts.json",
    "schema_registry": "metadata/schema_registry.json",
    "quality_report": "data_quality/reports/{silver_dataset}_quality_report.json",
    "catalog": "metadata/data_catalog.json",
    "pii_classification": "security/data_classification.json",
    "slo_report": "observability/reports/slo_report.json",
    "semantic_validation": "semantic_layer/reports/semantic_validation_report.json",
    "reconciliation": "data_quality/reports/reconciliation_report.json",
    "certification": "operations/certification/data_product_certification_report.json",
    "release_gate": "operations/release/release_gate_report.json",
    "audit_manifest": "metadata/audit_manifest.json",
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def exists(project_root: Path, relative_path: str) -> bool:
    return (project_root / relative_path).exists()


def generate_control_coverage(project_root: Path) -> dict[str, Any]:
    contracts = read_json(project_root / "contracts/source_contracts.json", {})
    catalog = read_json(project_root / "metadata/data_catalog.json", [])
    classifications = read_json(project_root / "security/data_classification.json", {})
    gold_datasets = sorted(path.stem for path in (project_root / "gold_layer").glob("gold_*.csv"))
    silver_datasets = sorted(path.stem for path in (project_root / "silver_layer").glob("silver_*.csv"))

    source_rows = []
    for source_system in sorted(contracts):
        source_rows.append(
            {
                "entity": source_system,
                "entity_type": "source",
                "source_contract": True,
                "schema_registry": exists(project_root, CONTROL_FILES["schema_registry"]),
                "quality_report": exists(
                    project_root,
                    CONTROL_FILES["quality_report"].format(silver_dataset=f"silver_{source_system}"),
                ),
                "catalog": False,
                "pii_classification": f"silver_{source_system}" in classifications,
                "slo_report": exists(project_root, CONTROL_FILES["slo_report"]),
            }
        )

    catalog_names = {entry["dataset_name"] for entry in catalog}
    gold_rows = []
    for dataset in gold_datasets:
        gold_rows.append(
            {
                "entity": dataset,
                "entity_type": "gold_dataset",
                "catalog": dataset in catalog_names,
                "pii_classification": dataset in classifications,
                "semantic_validation": exists(project_root, CONTROL_FILES["semantic_validation"]),
                "reconciliation": exists(project_root, CONTROL_FILES["reconciliation"]),
                "certification": exists(project_root, CONTROL_FILES["certification"]),
                "release_gate": exists(project_root, CONTROL_FILES["release_gate"]),
                "audit_manifest": exists(project_root, CONTROL_FILES["audit_manifest"]),
            }
        )

    rows = source_rows + gold_rows
    boolean_values = [
        value
        for row in rows
        for key, value in row.items()
        if key not in {"entity", "entity_type"} and isinstance(value, bool)
    ]
    coverage_pct = round(sum(1 for value in boolean_values if value) / len(boolean_values), 4) if boolean_values else 0.0
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_count": len(source_rows),
        "silver_dataset_count": len(silver_datasets),
        "gold_dataset_count": len(gold_rows),
        "control_coverage_pct": coverage_pct,
        "rows": rows,
    }
    output_dir = project_root / "metadata/control_coverage"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "control_coverage_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(output_dir / "control_coverage_report.md", report)
    return report


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Control Coverage Report",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        f"- Control coverage: `{report['control_coverage_pct']}`",
        f"- Sources: `{report['source_count']}`",
        f"- Gold datasets: `{report['gold_dataset_count']}`",
        "",
        "| Entity | Type | Covered Controls | Missing Controls |",
        "|---|---|---|---|",
    ]
    for row in report["rows"]:
        covered = sorted(key for key, value in row.items() if isinstance(value, bool) and value)
        missing = sorted(key for key, value in row.items() if isinstance(value, bool) and not value)
        lines.append(
            f"| {row['entity']} | {row['entity_type']} | {', '.join(covered)} | {', '.join(missing)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
