from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def generate_backfill_manifest(project_root: Path) -> dict[str, Any]:
    bronze_root = project_root / "raw_data/bronze"
    candidates = []
    for file_path in sorted(bronze_root.rglob("*.jsonl")):
        parts = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in file_path.parts if "=" in item}
        candidates.append(
            {
                "source_system": parts.get("source_system", "unknown"),
                "ingest_date": parts.get("ingest_date", "unknown"),
                "batch_id": parts.get("batch_id", "unknown"),
                "bronze_file": str(file_path.relative_to(project_root)),
                "recommended_replay_steps": [
                    "reprocess bronze file through silver standardizer",
                    "rerun quality checks for affected silver dataset",
                    "rebuild dependent gold marts",
                    "recompute readiness, SLO, alerts, and incident summary",
                ],
            }
        )
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "replay_scope": "bronze_partition",
        "candidates": candidates,
    }
    output_path = project_root / "operations/replay/backfill_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
