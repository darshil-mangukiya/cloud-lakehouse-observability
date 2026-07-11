from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTES = {
    "critical": ["pagerduty:data-platform-primary", "slack:#data-incidents"],
    "high": ["slack:#data-incidents"],
    "medium": ["slack:#data-quality"],
    "low": ["email:data-platform@example.com"],
}


def load_alerts(alert_log_path: Path) -> list[dict[str, Any]]:
    if not alert_log_path.exists():
        return []
    return [json.loads(line) for line in alert_log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_notification(alert: dict[str, Any], route: str) -> dict[str, Any]:
    return {
        "notification_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "alert_id": alert["alert_id"],
        "severity": alert["severity"],
        "alert_type": alert["alert_type"],
        "dataset_name": alert["dataset_name"],
        "message": f"{alert['severity'].upper()} {alert['alert_type']} on {alert['dataset_name']}: {alert['business_impact']}",
        "recommended_action": alert["recommended_action"],
        "delivery_status": "queued",
    }


def route_alerts(alert_log_path: Path, outbox_path: Path) -> list[dict[str, Any]]:
    alerts = [alert for alert in load_alerts(alert_log_path) if alert.get("resolution_status") == "open"]
    notifications = []
    for alert in alerts:
        for route in ROUTES.get(alert.get("severity", "low"), ROUTES["low"]):
            notifications.append(build_notification(alert, route))
    outbox_path.parent.mkdir(parents=True, exist_ok=True)
    with outbox_path.open("w", encoding="utf-8") as handle:
        for notification in notifications:
            handle.write(json.dumps(notification, sort_keys=True) + "\n")
    return notifications
