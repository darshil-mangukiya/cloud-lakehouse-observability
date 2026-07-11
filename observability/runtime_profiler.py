from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


class RuntimeProfiler:
    def __init__(self) -> None:
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._pipeline_start = perf_counter()
        self.steps: list[dict[str, Any]] = []

    def start_step(self, step_name: str) -> float:
        return perf_counter()

    def end_step(self, step_name: str, started: float, metadata: dict[str, Any] | None = None) -> None:
        duration_seconds = round(perf_counter() - started, 4)
        self.steps.append(
            {
                "step_name": step_name,
                "duration_seconds": duration_seconds,
                "metadata": metadata or {},
            }
        )

    def report(self) -> dict[str, Any]:
        total_duration = round(perf_counter() - self._pipeline_start, 4)
        slowest_steps = sorted(self.steps, key=lambda step: step["duration_seconds"], reverse=True)[:5]
        return {
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "total_duration_seconds": total_duration,
            "step_count": len(self.steps),
            "slowest_steps": slowest_steps,
            "steps": self.steps,
        }


def write_runtime_report(project_root: Path, profiler: RuntimeProfiler) -> dict[str, Any]:
    report = profiler.report()
    output_path = project_root / "observability/reports/runtime/runtime_profile.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
