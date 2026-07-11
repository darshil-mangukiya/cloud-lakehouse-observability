from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PII_COLUMN_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bcustomer_id\b",
        r"\buser_id\b",
        r"\bticket_id\b",
        r"\bsession_id\b",
        r"\bemail\b",
        r"\bphone\b",
        r"\bname\b",
        r"\baddress\b",
    ]
]

VALUE_PATTERNS = {
    "email": re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE),
    "phone": re.compile(r"^\+?[0-9][0-9\-\s]{7,}$"),
}


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def sample_rows(path: Path, limit: int = 25) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(row)
            if len(rows) >= limit:
                break
        return rows


def is_pii_column(column: str) -> bool:
    return any(pattern.search(column) for pattern in PII_COLUMN_PATTERNS)


def detected_value_types(rows: list[dict[str, str]], column: str) -> list[str]:
    detected = set()
    for row in rows:
        value = str(row.get(column, "")).strip()
        if not value:
            continue
        for value_type, pattern in VALUE_PATTERNS.items():
            if pattern.search(value):
                detected.add(value_type)
    return sorted(detected)


def scan_dataset(path: Path, project_root: Path, classification: dict[str, Any]) -> dict[str, Any]:
    dataset_name = path.stem
    header = read_header(path)
    rows = sample_rows(path)
    detected_columns = sorted(column for column in header if is_pii_column(column))
    value_findings = {
        column: detected_value_types(rows, column)
        for column in header
        if detected_value_types(rows, column)
    }
    expected_pii = set(classification.get(dataset_name, {}).get("pii_columns", []))
    unexpected_pii = sorted(set(detected_columns) - expected_pii)
    missing_classification = bool(detected_columns and dataset_name not in classification)
    status = "failed" if unexpected_pii or missing_classification else "passed"
    return {
        "dataset_name": dataset_name,
        "path": str(path.relative_to(project_root)),
        "classification": classification.get(dataset_name, {}).get("classification", "unclassified"),
        "expected_pii_columns": sorted(expected_pii),
        "detected_pii_columns": detected_columns,
        "unexpected_pii_columns": unexpected_pii,
        "detected_value_types": value_findings,
        "missing_classification": missing_classification,
        "status": status,
    }


def run_pii_scan(project_root: Path) -> dict[str, Any]:
    classification = json.loads((project_root / "security/data_classification.json").read_text(encoding="utf-8"))
    dataset_paths = sorted((project_root / "silver_layer").glob("*.csv")) + sorted((project_root / "gold_layer").glob("*.csv"))
    datasets = [scan_dataset(path, project_root, classification) for path in dataset_paths]
    report = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(datasets),
        "failed_dataset_count": sum(1 for dataset in datasets if dataset["status"] == "failed"),
        "status": "failed" if any(dataset["status"] == "failed" for dataset in datasets) else "passed",
        "datasets": datasets,
    }
    output_path = project_root / "security/pii_scan_report.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
