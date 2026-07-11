from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ingestion.schema_registry import SchemaRegistry


class SchemaRegistryTests(unittest.TestCase):
    def test_safe_rename_is_compatible_evolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(Path(tmpdir) / "schema_registry.json")
            registry.register(
                "ecommerce_transactions",
                [
                    {
                        "transaction_id": "T1",
                        "customer_id": "C1",
                        "order_ts": "2026-05-10T00:00:00Z",
                        "amount": "10.00",
                    }
                ],
            )
            report = registry.register(
                "ecommerce_transactions",
                [
                    {
                        "order_id": "T2",
                        "customer_id": "C2",
                        "order_timestamp": "2026-05-11T00:00:00Z",
                        "order_value": "11.00",
                        "coupon_code": "VIP",
                    }
                ],
            )
            self.assertEqual(report.status, "compatible_evolution")
            self.assertFalse(report.breaking)
            self.assertEqual(report.safe_renames["order_id"], "transaction_id")
            self.assertEqual(report.safe_renames["order_value"], "amount")
            self.assertIn("coupon_code", report.added_columns)

    def test_type_change_is_breaking(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = SchemaRegistry(Path(tmpdir) / "schema_registry.json")
            registry.register("targets_planning", [{"target_date": "2026-05-10", "revenue_target": "100"}])
            report = registry.register("targets_planning", [{"target_date": "2026-05-11", "revenue_target": "not-a-number"}])
            self.assertTrue(report.breaking)
            self.assertIn("revenue_target", report.type_changes)


if __name__ == "__main__":
    unittest.main()
