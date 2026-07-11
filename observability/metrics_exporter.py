from __future__ import annotations

from pathlib import Path
from typing import Any


def export_prometheus_metrics(readiness_records: list[dict[str, Any]], output_path: Path) -> Path:
    lines = [
        "# HELP lakehouse_dataset_readiness_score Dataset readiness score between 0 and 1.",
        "# TYPE lakehouse_dataset_readiness_score gauge",
    ]
    for record in readiness_records:
        dataset = record["dataset_name"]
        lines.append(f'lakehouse_dataset_readiness_score{{dataset="{dataset}"}} {record["readiness_score"]}')
        lines.append(f'lakehouse_dataset_rows{{dataset="{dataset}"}} {record["row_count"]}')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
