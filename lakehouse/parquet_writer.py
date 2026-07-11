from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


VALID_LAYERS = {"bronze", "silver", "gold"}


@dataclass
class ParquetWriteResult:
    layer: str
    dataset_name: str
    row_count: int
    output_path: str
    status: str
    message: str


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sanitize_partition_value(value: str) -> str:
    cleaned = str(value).strip().replace(" ", "_").replace("/", "_")
    return cleaned or "unknown"


def build_partition_path(
    storage_root: Path,
    *,
    layer: str,
    dataset_name: str | None = None,
    source_system: str | None = None,
    load_date: str | None = None,
    batch_id: str | None = None,
) -> Path:
    if layer not in VALID_LAYERS:
        raise ValueError(f"Unsupported lakehouse layer: {layer}")
    if layer == "bronze" and not source_system:
        raise ValueError("bronze Parquet partitions require source_system")
    if layer in {"silver", "gold"} and not dataset_name:
        raise ValueError(f"{layer} Parquet partitions require dataset_name")

    partition_date = sanitize_partition_value(load_date or utc_date())
    path = storage_root / layer
    if layer == "bronze":
        path = path / f"source_system={sanitize_partition_value(source_system or 'unknown')}"
    else:
        path = path / f"dataset={sanitize_partition_value(dataset_name or 'unknown')}"
    path = path / f"load_date={partition_date}"
    if batch_id:
        path = path / f"batch_id={sanitize_partition_value(batch_id)}"
    return path


def write_partitioned_parquet(
    records: list[dict[str, Any]],
    storage_root: Path,
    *,
    layer: str,
    dataset_name: str,
    source_system: str | None = None,
    load_date: str | None = None,
    batch_id: str | None = None,
) -> ParquetWriteResult:
    output_dir = build_partition_path(
        storage_root,
        layer=layer,
        dataset_name=dataset_name,
        source_system=source_system,
        load_date=load_date,
        batch_id=batch_id,
    )
    output_path = output_dir / "part-00000.parquet"
    frame = pd.DataFrame(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    if frame.empty:
        return ParquetWriteResult(layer, dataset_name, 0, str(output_path), "skipped", "No records to write.")
    try:
        frame.to_parquet(output_path, index=False)
    except (ImportError, ValueError) as exc:
        return ParquetWriteResult(
            layer=layer,
            dataset_name=dataset_name,
            row_count=len(frame),
            output_path=str(output_path),
            status="skipped",
            message=f"Parquet engine unavailable: {exc}",
        )
    return ParquetWriteResult(
        layer=layer,
        dataset_name=dataset_name,
        row_count=len(frame),
        output_path=str(output_path),
        status="written",
        message="Partitioned Parquet file written.",
    )


def export_lakehouse_parquet(
    project_root: Path,
    *,
    bronze_records: dict[str, list[dict[str, Any]]],
    silver: dict[str, list[dict[str, Any]]],
    gold: dict[str, list[dict[str, Any]]],
    batch_id: str,
    load_date: str | None = None,
) -> dict[str, Any]:
    storage_root = project_root / "lakehouse_storage"
    results: list[ParquetWriteResult] = []

    for source_system, records in bronze_records.items():
        results.append(
            write_partitioned_parquet(
                records,
                storage_root,
                layer="bronze",
                dataset_name=source_system,
                source_system=source_system,
                load_date=load_date,
                batch_id=batch_id,
            )
        )
    for dataset_name, records in silver.items():
        results.append(
            write_partitioned_parquet(
                records,
                storage_root,
                layer="silver",
                dataset_name=dataset_name,
                load_date=load_date,
                batch_id=batch_id,
            )
        )
    for dataset_name, records in gold.items():
        results.append(
            write_partitioned_parquet(
                records,
                storage_root,
                layer="gold",
                dataset_name=dataset_name,
                load_date=load_date,
                batch_id=batch_id,
            )
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_root": str(storage_root.relative_to(project_root)),
        "layout": "layer/(source_system|dataset)/load_date[/batch_id]/part-00000.parquet",
        "written_count": sum(1 for result in results if result.status == "written"),
        "skipped_count": sum(1 for result in results if result.status == "skipped"),
        "results": [asdict(result) for result in results],
    }
    output_path = project_root / "observability/reports/parquet_export_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

