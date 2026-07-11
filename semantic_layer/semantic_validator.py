from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - fallback keeps local smoke path dependency-light.
    yaml = None


def _load_metrics_yml(path: Path) -> dict[str, Any]:
    if yaml is None:
        return _minimal_metrics_parser(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _minimal_metrics_parser(path: Path) -> dict[str, Any]:
    metrics = []
    current: dict[str, Any] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- name:"):
            if current:
                metrics.append(current)
            current = {"name": line.split(":", 1)[1].strip()}
        elif current and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        metrics.append(current)
    return {"metrics": metrics, "dimensions": []}


def csv_columns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return set(next(reader, []))


def dataset_columns(project_root: Path, dataset: str) -> set[str]:
    if dataset.startswith("gold_"):
        return csv_columns(project_root / "gold_layer" / f"{dataset}.csv")
    if dataset.startswith("observability."):
        if dataset.endswith("dataset_readiness"):
            return {"dataset_name", "readiness_score", "readiness_status", "quality_status", "freshness_status", "schema_status"}
    if dataset.startswith("metadata."):
        if dataset.endswith("data_catalog"):
            return {"dataset_name", "layer", "owner", "source_system", "criticality_tier", "business_description"}
    return set()


def validate_semantic_layer(project_root: Path) -> dict[str, Any]:
    payload = _load_metrics_yml(project_root / "semantic_layer/metrics.yml")
    failures = []
    metric_results = []
    for metric in payload.get("metrics", []):
        dataset = metric["dataset"]
        columns = dataset_columns(project_root, dataset)
        required = []
        if "expression" in metric:
            required.append(metric["expression"])
        if "numerator" in metric:
            required.append(metric["numerator"])
        if "denominator" in metric:
            required.append(metric["denominator"])
        missing = sorted(column for column in required if column not in columns)
        status = "failed" if missing else "passed"
        if missing:
            failures.append({"metric": metric["name"], "dataset": dataset, "missing_columns": missing})
        metric_results.append(
            {
                "metric": metric["name"],
                "dataset": dataset,
                "status": status,
                "required_columns": required,
                "missing_columns": missing,
            }
        )

    report = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "metric_count": len(payload.get("metrics", [])),
        "failed_metric_count": len(failures),
        "status": "failed" if failures else "passed",
        "metrics": metric_results,
    }
    output_path = project_root / "semantic_layer/reports/semantic_validation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
