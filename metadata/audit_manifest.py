from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_ROOTS = [
    "silver_layer",
    "gold_layer",
    "data_quality/reports",
    "observability/reports",
    "alerts",
    "lineage",
    "semantic_layer/reports",
    "security",
    "operations/replay",
    "operations/certification",
    "operations/release",
    "operations/remediation",
    "operations/scenarios",
    "operations/preflight",
    "operations/sbom",
    "metadata/control_coverage",
    "metadata/data_catalog.json",
    "metadata/schema_registry.json",
    "metadata/load_log.csv",
]
AUDIT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".prom"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return max(sum(1 for _ in csv.reader(handle)) - 1, 0)
    if suffix == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if suffix == ".json":
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            for key in ("checks", "metrics", "layers", "candidates", "source_slos", "gold_slos"):
                if isinstance(payload.get(key), list):
                    return len(payload[key])
        return None
    return None


def iter_audit_files(project_root: Path) -> list[Path]:
    files: list[Path] = []
    for relative in AUDIT_ROOTS:
        root = project_root / relative
        if root.is_file():
            files.append(root)
        elif root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(
        {
            path
            for path in files
            if path.name != "audit_manifest.json" and path.suffix.lower() in AUDIT_SUFFIXES
        }
    )


def generate_audit_manifest(project_root: Path) -> dict[str, Any]:
    artifacts = []
    for path in iter_audit_files(project_root):
        artifacts.append(
            {
                "path": str(path.relative_to(project_root)),
                "size_bytes": path.stat().st_size,
                "row_count": row_count(path),
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "total_size_bytes": sum(item["size_bytes"] for item in artifacts),
        "artifacts": artifacts,
    }
    output_path = project_root / "metadata/audit_manifest.json"
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
