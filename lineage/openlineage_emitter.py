from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def emit_event(
    event_path: Path,
    event_type: str,
    job_name: str,
    batch_id: str,
    inputs: list[str],
    outputs: list[str],
    facets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "eventId": str(uuid.uuid4()),
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "eventType": event_type,
        "producer": "p5-cloud-lakehouse-observability",
        "job": {"namespace": "local.lakehouse", "name": job_name},
        "run": {"runId": batch_id},
        "inputs": [{"namespace": "local.lakehouse", "name": item} for item in inputs],
        "outputs": [{"namespace": "local.lakehouse", "name": item} for item in outputs],
        "facets": facets or {},
    }
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event
