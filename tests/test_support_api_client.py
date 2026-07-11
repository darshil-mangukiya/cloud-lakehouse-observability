from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ingestion.api_sources.support_api_client import ingest_support_api, validate_ticket


class SupportApiClientTests(unittest.TestCase):
    def test_validate_ticket_rejects_missing_primary_key(self) -> None:
        valid, reason = validate_ticket({"ticket_id": "", "customer_id": "c001", "created_ts": "2026-05-11T09:00:00Z"})

        self.assertFalse(valid)
        self.assertIn("ticket_id", reason)

    def test_paginated_ingestion_writes_accepted_and_rejected_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            summary = ingest_support_api(project_root, batch_id="batch_001")

            self.assertEqual(summary["request_count"], 2)
            self.assertEqual(summary["accepted_count"], 3)
            self.assertEqual(summary["rejected_count"], 1)
            self.assertTrue((project_root / summary["bronze_path"]).exists())
            self.assertTrue((project_root / summary["rejected_path"]).exists())


if __name__ == "__main__":
    unittest.main()

