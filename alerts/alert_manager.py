from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Alert:
    alert_id: str
    timestamp: str
    severity: str
    alert_type: str
    dataset_name: str
    source_system: str
    business_impact: str
    recommended_action: str
    resolution_status: str


class AlertManager:
    def __init__(self, alert_log_path: Path):
        self.alert_log_path = alert_log_path
        self.alert_log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        severity: str,
        alert_type: str,
        dataset_name: str,
        source_system: str,
        business_impact: str,
        recommended_action: str,
        resolution_status: str = "open",
    ) -> Alert:
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            alert_type=alert_type,
            dataset_name=dataset_name,
            source_system=source_system,
            business_impact=business_impact,
            recommended_action=recommended_action,
            resolution_status=resolution_status,
        )
        with self.alert_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(alert), sort_keys=True) + "\n")
        self._write_postgres(alert)
        return alert

    def _write_postgres(self, alert: Alert) -> None:
        dsn = os.getenv("ALERT_POSTGRES_DSN")
        if not dsn:
            return
        try:
            import psycopg2
        except ImportError:
            return
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into alerts.alert_log (
                        alert_id, timestamp, severity, alert_type, dataset_name,
                        source_system, business_impact, recommended_action, resolution_status
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (alert_id) do nothing
                    """,
                    (
                        alert.alert_id,
                        alert.timestamp,
                        alert.severity,
                        alert.alert_type,
                        alert.dataset_name,
                        alert.source_system,
                        alert.business_impact,
                        alert.recommended_action,
                        alert.resolution_status,
                    ),
                )

    def read_alerts(self) -> list[dict[str, str]]:
        if not self.alert_log_path.exists():
            return []
        alerts = []
        with self.alert_log_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    alerts.append(json.loads(line))
        return alerts
