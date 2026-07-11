from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipelines.run_platform import run


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SmokePipelineTests(unittest.TestCase):
    def test_pipeline_builds_gold_outputs_and_alerts(self) -> None:
        summary = run(PROJECT_ROOT, reset=True)

        self.assertEqual(summary["bronze_sources"]["ecommerce_transactions"], 9)
        self.assertIn("gold_revenue_analytics", summary["gold_datasets"])
        self.assertTrue((PROJECT_ROOT / "gold_layer/gold_revenue_analytics.csv").exists())
        self.assertTrue((PROJECT_ROOT / "metadata/schema_registry.json").exists())
        self.assertTrue((PROJECT_ROOT / "metadata/contract_reports/ecommerce_transactions/orders_2026_05_10_schema_v2_contract_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/dataset_readiness.json").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/slo_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/incidents/latest_incident_summary.md").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/finops/storage_cost_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "data_quality/reports/reconciliation_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "metadata/audit_manifest.json").exists())
        self.assertTrue((PROJECT_ROOT / "metadata/catalog_validation_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "lineage/lineage_graph.json").exists())
        self.assertTrue((PROJECT_ROOT / "lineage/lineage_graph.md").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/runtime/runtime_profile.json").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/parquet_export_manifest.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/certification/data_product_certification_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/release/release_gate_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/exceptions/exception_evaluation_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/remediation/remediation_plan.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/scenarios/scenario_catalog.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/preflight/preflight_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "operations/sbom/software_inventory.json").exists())
        self.assertTrue((PROJECT_ROOT / "metadata/control_coverage/control_coverage_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "docs/FINAL_PROJECT_HANDOFF.md").exists())
        self.assertTrue((PROJECT_ROOT / "observability/reports/scorecards/platform_trust_scorecard.json").exists())
        self.assertTrue((PROJECT_ROOT / "security/pii_scan_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "semantic_layer/reports/semantic_validation_report.json").exists())
        self.assertTrue((PROJECT_ROOT / "security/access_policy_matrix.md").exists())
        self.assertTrue((PROJECT_ROOT / "operations/replay/backfill_manifest.json").exists())
        self.assertTrue((PROJECT_ROOT / "alerts/notification_outbox.jsonl").exists())
        self.assertTrue((PROJECT_ROOT / "lineage/events.jsonl").exists())
        self.assertGreaterEqual(summary["notifications_enqueued"], 1)
        self.assertEqual(summary["semantic_validation_status"], "passed")
        self.assertEqual(summary["reconciliation_status"], "passed")
        self.assertEqual(summary["pii_scan_status"], "passed")
        self.assertEqual(summary["catalog_validation_status"], "passed")
        self.assertEqual(summary["certification_status"], "blocked")
        self.assertEqual(summary["release_status"], "blocked")
        self.assertEqual(summary["exception_status"], "failed")
        self.assertGreater(summary["remediation_tasks"], 1)
        self.assertGreater(summary["trust_score"], 0)
        self.assertGreater(summary["control_coverage_pct"], 0)
        self.assertGreaterEqual(summary["scenario_count"], 5)
        self.assertIn(summary["preflight_status"], {"passed", "passed_with_warnings"})
        self.assertGreater(summary["software_inventory_packages"], 1)
        self.assertEqual(summary["handoff_path"], "docs/FINAL_PROJECT_HANDOFF.md")
        self.assertGreater(summary["audit_artifacts"], 1)
        self.assertGreater(summary["lineage_graph_nodes"], 1)
        self.assertGreaterEqual(summary["pipeline_duration_seconds"], 0)
        self.assertIn("parquet_written_count", summary)
        self.assertIn("parquet_skipped_count", summary)

        alerts_path = PROJECT_ROOT / "alerts/alert_log.jsonl"
        alerts = [json.loads(line) for line in alerts_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(alerts), 1)
        self.assertTrue(any(alert["alert_type"] in {"quality_failure", "rejected_records"} for alert in alerts))


if __name__ == "__main__":
    unittest.main()
