from __future__ import annotations

import unittest
from pathlib import Path

from observability.runtime_profiler import RuntimeProfiler
from operations.certification_manager import certify_data_products


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CertificationRuntimeTests(unittest.TestCase):
    def test_certification_report_contains_products(self) -> None:
        report = certify_data_products(PROJECT_ROOT)
        self.assertGreaterEqual(report["product_count"], 4)
        self.assertIn(report["status"], {"passed", "blocked"})

    def test_runtime_profiler_records_steps(self) -> None:
        profiler = RuntimeProfiler()
        started = profiler.start_step("unit_test_step")
        profiler.end_step("unit_test_step", started, {"ok": True})
        report = profiler.report()
        self.assertEqual(report["step_count"], 1)
        self.assertEqual(report["steps"][0]["step_name"], "unit_test_step")


if __name__ == "__main__":
    unittest.main()
