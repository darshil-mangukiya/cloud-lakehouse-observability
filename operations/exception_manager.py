from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_active(exception: dict[str, Any], now: datetime) -> bool:
    if exception.get("status") != "active":
        return False
    expires_at = parse_time(exception["expires_at"])
    return expires_at >= now


def applies_to_gate(exception: dict[str, Any], gate: dict[str, Any]) -> bool:
    return exception.get("gate_name") in {gate["gate_name"], "*"}


def evaluate_exceptions(project_root: Path) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    register = read_json(project_root / "operations/exceptions/exception_register.json", {"exceptions": []})
    release = read_json(project_root / "operations/release/release_gate_report.json", {"gates": []})
    active_exceptions = [exception for exception in register["exceptions"] if is_active(exception, now)]
    evaluated = []
    for gate in release.get("gates", []):
        if gate.get("status") == "passed":
            continue
        matched = [exception for exception in active_exceptions if applies_to_gate(exception, gate)]
        evaluated.append(
            {
                "gate_name": gate["gate_name"],
                "gate_status": gate["status"],
                "gate_severity": gate["severity"],
                "exception_applied": bool(matched),
                "exception_ids": [exception["exception_id"] for exception in matched],
            }
        )

    unresolved_without_exception = [
        item
        for item in evaluated
        if item["gate_status"] == "failed" and item["gate_severity"] in {"critical", "high"} and not item["exception_applied"]
    ]
    report = {
        "evaluated_at": now.isoformat(),
        "active_exception_count": len(active_exceptions),
        "evaluated_gate_count": len(evaluated),
        "unresolved_without_exception_count": len(unresolved_without_exception),
        "status": "failed" if unresolved_without_exception else "passed",
        "exceptions": active_exceptions,
        "gates": evaluated,
    }
    output_path = project_root / "operations/exceptions/exception_evaluation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
