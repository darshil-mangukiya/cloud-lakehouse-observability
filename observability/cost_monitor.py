from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LAYER_PATHS = {
    "bronze": "raw_data/bronze",
    "silver": "silver_layer",
    "gold": "gold_layer",
    "quality_reports": "data_quality/reports",
    "observability_reports": "observability/reports",
    "dashboard_exports": "dashboards/exports",
}


def path_size_bytes(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    if path.is_file():
        return path.stat().st_size, 1
    total_bytes = 0
    file_count = 0
    for file_path in path.rglob("*"):
        if file_path.is_file():
            total_bytes += file_path.stat().st_size
            file_count += 1
    return total_bytes, file_count


def estimate_monthly_storage_cost(size_bytes: int, usd_per_gb_month: float = 0.023) -> float:
    gib = size_bytes / (1024**3)
    return round(gib * usd_per_gb_month, 6)


def generate_cost_report(project_root: Path) -> dict[str, Any]:
    layers = []
    total_bytes = 0
    total_files = 0
    for layer, relative_path in LAYER_PATHS.items():
        size_bytes, file_count = path_size_bytes(project_root / relative_path)
        total_bytes += size_bytes
        total_files += file_count
        layers.append(
            {
                "layer": layer,
                "path": relative_path,
                "file_count": file_count,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024**2), 4),
                "estimated_s3_standard_monthly_cost_usd": estimate_monthly_storage_cost(size_bytes),
            }
        )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pricing_note": "Estimated with S3 Standard storage at $0.023 per GB-month; excludes requests, compute, and transfer.",
        "total_files": total_files,
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024**2), 4),
        "estimated_s3_standard_monthly_cost_usd": estimate_monthly_storage_cost(total_bytes),
        "layers": layers,
    }
    output_path = project_root / "observability/reports/finops/storage_cost_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
