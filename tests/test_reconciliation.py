from __future__ import annotations

import unittest
from pathlib import Path

from data_quality.reconciliation import reconcile_gold_outputs
from metadata.audit_manifest import generate_audit_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReconciliationAndAuditTests(unittest.TestCase):
    def test_reconciliation_passes_for_generated_gold(self) -> None:
        report = reconcile_gold_outputs(PROJECT_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["failed_check_count"], 0)

    def test_audit_manifest_has_artifact_checksums(self) -> None:
        manifest = generate_audit_manifest(PROJECT_ROOT)
        self.assertGreater(manifest["artifact_count"], 1)
        self.assertTrue(all("sha256" in artifact for artifact in manifest["artifacts"]))


if __name__ == "__main__":
    unittest.main()
