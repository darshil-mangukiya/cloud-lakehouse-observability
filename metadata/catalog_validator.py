from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "dataset_name",
    "layer",
    "owner",
    "source_system",
    "business_description",
    "downstream_usage",
    "refresh_frequency",
    "criticality_tier",
]


def validate_catalog(project_root: Path) -> dict[str, Any]:
    catalog_path = project_root / "metadata/data_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else []
    gold_datasets = {path.stem for path in (project_root / "gold_layer").glob("gold_*.csv")}
    catalog_datasets = {entry.get("dataset_name") for entry in catalog}

    entry_results = []
    for entry in catalog:
        missing_fields = [field for field in REQUIRED_FIELDS if not entry.get(field)]
        entry_results.append(
            {
                "dataset_name": entry.get("dataset_name"),
                "missing_fields": missing_fields,
                "status": "failed" if missing_fields else "passed",
            }
        )

    missing_gold_catalog_entries = sorted(gold_datasets - catalog_datasets)
    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_entry_count": len(catalog),
        "gold_dataset_count": len(gold_datasets),
        "missing_gold_catalog_entries": missing_gold_catalog_entries,
        "failed_entry_count": sum(1 for entry in entry_results if entry["status"] == "failed"),
        "status": "failed" if missing_gold_catalog_entries or any(entry["status"] == "failed" for entry in entry_results) else "passed",
        "entries": entry_results,
    }
    output_path = project_root / "metadata/catalog_validation_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
