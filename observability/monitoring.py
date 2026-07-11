from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DatasetStateStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.payload = self._load()

    def _load(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"datasets": {}}

    def history(self, dataset_name: str) -> list[dict[str, Any]]:
        return self.payload["datasets"].get(dataset_name, [])

    def append(self, dataset_name: str, metrics: dict[str, Any]) -> None:
        self.payload["datasets"].setdefault(dataset_name, []).append(metrics)
        self.state_path.write_text(json.dumps(self.payload, indent=2), encoding="utf-8")


def row_count_anomaly(dataset_name: str, row_count: int, store: DatasetStateStore, warn_pct: float = 0.35) -> dict[str, Any]:
    history = store.history(dataset_name)
    previous_counts = [item["row_count"] for item in history[-7:] if "row_count" in item]
    baseline = mean(previous_counts) if previous_counts else row_count
    delta_pct = 0.0 if baseline == 0 else abs(row_count - baseline) / baseline
    status = "failed" if previous_counts and delta_pct > warn_pct else "passed"
    return {
        "metric": "row_count_anomaly",
        "dataset_name": dataset_name,
        "status": status,
        "row_count": row_count,
        "baseline_row_count": round(baseline, 2),
        "delta_pct": round(delta_pct, 4),
        "threshold": warn_pct,
    }


def build_readiness_record(dataset_name: str, row_count: int, quality_status: str, freshness_status: str, schema_status: str) -> dict[str, Any]:
    component_scores = {
        "has_rows": 1.0 if row_count > 0 else 0.0,
        "quality": 1.0 if quality_status == "passed" else 0.0,
        "freshness": 1.0 if freshness_status == "passed" else 0.0,
        "schema": 1.0 if schema_status in {"unchanged", "new_schema", "compatible_evolution"} else 0.0,
    }
    readiness_score = round(sum(component_scores.values()) / len(component_scores), 4)
    return {
        "dataset_name": dataset_name,
        "evaluated_at": utc_now(),
        "row_count": row_count,
        "quality_status": quality_status,
        "freshness_status": freshness_status,
        "schema_status": schema_status,
        "readiness_score": readiness_score,
        "readiness_status": "ready" if readiness_score >= 0.95 else "at_risk",
        "component_scores": component_scores,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
