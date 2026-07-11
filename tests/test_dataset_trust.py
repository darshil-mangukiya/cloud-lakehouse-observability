from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from observability.dataset_trust import build_dataset_trust_scores


class DatasetTrustTests(unittest.TestCase):
    def test_dataset_trust_score_produces_reason_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "observability/reports").mkdir(parents=True)
            (root / "metadata").mkdir()
            (root / "alerts").mkdir()
            (root / "lineage").mkdir()

            (root / "observability/reports/dataset_readiness.json").write_text(
                json.dumps(
                    [
                        {
                            "dataset_name": "gold_revenue_analytics",
                            "readiness_score": 0.75,
                            "quality_status": "failed",
                            "freshness_status": "passed",
                            "schema_status": "compatible_evolution",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (root / "observability/reports/slo_report.json").write_text(
                json.dumps({"gold_slos": [{"dataset_name": "gold_revenue_analytics", "slo_status": "failed"}]}),
                encoding="utf-8",
            )
            (root / "observability/reports/row_count_anomalies.json").write_text(
                json.dumps([{"dataset_name": "gold_revenue_analytics", "status": "failed"}]),
                encoding="utf-8",
            )
            (root / "metadata/data_catalog.json").write_text(
                json.dumps(
                    [
                        {
                            "dataset_name": "gold_revenue_analytics",
                            "owner": "finance-analytics",
                            "business_description": "Daily revenue mart.",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (root / "alerts/alert_log.jsonl").write_text(
                json.dumps(
                    {
                        "severity": "critical",
                        "dataset_name": "gold_revenue_analytics",
                        "resolution_status": "open",
                        "business_impact": "gold_revenue_analytics blocked",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "lineage/events.jsonl").write_text(
                json.dumps({"outputs": ["gold_revenue_analytics"], "inputs": ["silver_ecommerce_transactions"]}) + "\n",
                encoding="utf-8",
            )

            report = build_dataset_trust_scores(root)
            dataset = report["datasets"][0]

            self.assertEqual(report["dataset_count"], 1)
            self.assertIn(dataset["trust_score_band"], {"At Risk", "Blocked"})
            self.assertIn("failed_quality_gate", dataset["reason_codes"])
            self.assertIn("critical_open_alert", dataset["reason_codes"])


if __name__ == "__main__":
    unittest.main()
