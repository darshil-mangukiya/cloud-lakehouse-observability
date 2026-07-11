from __future__ import annotations

import unittest
from pathlib import Path

from operations.exception_manager import evaluate_exceptions
from operations.remediation_manager import generate_remediation_plan


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ExceptionRemediationTests(unittest.TestCase):
    def test_exception_evaluation_reports_active_exceptions(self) -> None:
        report = evaluate_exceptions(PROJECT_ROOT)
        self.assertGreaterEqual(report["active_exception_count"], 1)
        self.assertIn(report["status"], {"passed", "failed"})

    def test_remediation_plan_generates_tasks_for_blocked_release(self) -> None:
        report = generate_remediation_plan(PROJECT_ROOT)
        self.assertGreater(report["task_count"], 0)
        self.assertTrue(all("owner" in task for task in report["tasks"]))


if __name__ == "__main__":
    unittest.main()
