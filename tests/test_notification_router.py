from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from alerts.notification_router import route_alerts


class NotificationRouterTests(unittest.TestCase):
    def test_critical_alert_routes_to_pagerduty_and_slack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            alert_path = Path(tmpdir) / "alert_log.jsonl"
            outbox_path = Path(tmpdir) / "notification_outbox.jsonl"
            alert = {
                "alert_id": "a-1",
                "severity": "critical",
                "alert_type": "quality_failure",
                "dataset_name": "gold_revenue_analytics",
                "business_impact": "Revenue reporting is blocked.",
                "recommended_action": "Fix quality failure and rerun.",
                "resolution_status": "open",
            }
            alert_path.write_text(json.dumps(alert) + "\n", encoding="utf-8")

            notifications = route_alerts(alert_path, outbox_path)

            self.assertEqual(len(notifications), 2)
            self.assertTrue(any(item["route"].startswith("pagerduty:") for item in notifications))
            self.assertTrue(any(item["route"].startswith("slack:") for item in notifications))


if __name__ == "__main__":
    unittest.main()
