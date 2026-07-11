from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ingestion.contract_validator import validate_contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_PATH = PROJECT_ROOT / "contracts/source_contracts.json"


class ContractValidatorTests(unittest.TestCase):
    def test_safe_renamed_columns_satisfy_required_contract(self) -> None:
        report = validate_contract(
            "ecommerce_transactions",
            [
                {
                    "order_id": "T100",
                    "customer_id": "C100",
                    "product_id": "P100",
                    "order_timestamp": "2026-05-10T00:00:00Z",
                    "order_value": "25.00",
                    "status": "completed",
                }
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["safe_renames_applied"]["order_id"], "transaction_id")

    def test_added_optional_column_is_allowed(self) -> None:
        report = validate_contract(
            "ecommerce_transactions",
            [
                {
                    "transaction_id": "T101",
                    "customer_id": "C101",
                    "product_id": "P100",
                    "order_ts": "2026-05-10T00:00:00Z",
                    "amount": "25.00",
                    "status": "completed",
                    "coupon_code": "SPRING10",
                }
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "PASS")

    def test_missing_required_column_fails_contract(self) -> None:
        report = validate_contract(
            "product_catalog",
            [{"product_id": "P1", "product_name": "Missing Category", "active_flag": "true"}],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["violations"][0]["check_name"], "required_columns_present")

    def test_type_change_fails_contract(self) -> None:
        report = validate_contract(
            "product_catalog",
            [
                {
                    "product_id": "P1",
                    "product_name": "Widget",
                    "category": "hardware",
                    "active_flag": "not-a-boolean",
                }
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("type_validation_active_flag", {violation["check_name"] for violation in report["violations"]})

    def test_null_explosion_quarantines_critical_source(self) -> None:
        report = validate_contract(
            "customer_behavior",
            [
                {"event_id": "E1", "customer_id": "", "event_ts": "2026-05-10T00:00:00Z", "event_type": "view"},
                {"event_id": "E2", "customer_id": "", "event_ts": "2026-05-10T00:01:00Z", "event_type": "view"},
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "QUARANTINE")
        self.assertIn("null_threshold_customer_id", {violation["check_name"] for violation in report["violations"]})

    def test_duplicate_primary_keys_quarantine_critical_source(self) -> None:
        report = validate_contract(
            "ecommerce_transactions",
            [
                {
                    "transaction_id": "T102",
                    "customer_id": "C102",
                    "product_id": "P100",
                    "order_ts": "2026-05-10T00:00:00Z",
                    "amount": "25.00",
                    "status": "completed",
                },
                {
                    "transaction_id": "T102",
                    "customer_id": "C103",
                    "product_id": "P100",
                    "order_ts": "2026-05-10T00:02:00Z",
                    "amount": "30.00",
                    "status": "completed",
                },
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "QUARANTINE")
        self.assertIn("primary_key_unique", {violation["check_name"] for violation in report["violations"]})

    def test_stale_source_file_fails_freshness_contract(self) -> None:
        validation_time = datetime(2026, 5, 10, 12, tzinfo=timezone.utc)
        observed_at = validation_time - timedelta(days=2)
        report = validate_contract(
            "marketing_campaigns",
            [
                {
                    "campaign_id": "CMP100",
                    "campaign_date": "2026-05-10",
                    "channel": "paid_search",
                    "spend": "100.00",
                }
            ],
            CONTRACTS_PATH,
            observed_at=observed_at.isoformat(),
            validation_time=validation_time.isoformat(),
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("freshness_sla", {violation["check_name"] for violation in report["violations"]})

    def test_breaking_schema_change_quarantines_critical_source(self) -> None:
        report = validate_contract(
            "ecommerce_transactions",
            [
                {
                    "transaction_id": "T103",
                    "product_id": "P100",
                    "order_ts": "2026-05-10T00:00:00Z",
                    "amount": "25.00",
                    "status": "completed",
                }
            ],
            CONTRACTS_PATH,
        )
        self.assertEqual(report["status"], "QUARANTINE")


if __name__ == "__main__":
    unittest.main()
