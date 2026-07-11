from __future__ import annotations

import unittest

from data_quality.validation_runner import validate_dataset


class QualityRunnerTests(unittest.TestCase):
    def test_duplicate_and_null_failures_are_reported(self) -> None:
        report = validate_dataset(
            "silver_ecommerce_transactions",
            [
                {
                    "transaction_id": "T1",
                    "customer_id": "C1",
                    "product_id": "P1",
                    "order_ts": "2026-05-10T00:00:00Z",
                    "amount": 10.0,
                    "status": "completed",
                },
                {
                    "transaction_id": "T1",
                    "customer_id": "",
                    "product_id": "P2",
                    "order_ts": "2026-05-10T01:00:00Z",
                    "amount": 12.0,
                    "status": "unknown",
                },
            ],
        )
        failed_checks = {result["check_name"] for result in report["results"] if result["status"] == "failed"}
        self.assertEqual(report["status"], "failed")
        self.assertIn("unique_transaction_id", failed_checks)
        self.assertIn("null_rate_customer_id", failed_checks)
        self.assertIn("accepted_values_status", failed_checks)


if __name__ == "__main__":
    unittest.main()
