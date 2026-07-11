from __future__ import annotations

import unittest
from pathlib import Path

from metadata.control_coverage import generate_control_coverage
from operations.handoff_generator import generate_final_handoff
from operations.scenario_simulator import generate_scenario_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class HandoffCoverageTests(unittest.TestCase):
    def test_control_coverage_reports_entities(self) -> None:
        report = generate_control_coverage(PROJECT_ROOT)
        self.assertGreater(report["source_count"], 0)
        self.assertGreater(report["gold_dataset_count"], 0)

    def test_scenario_catalog_has_expected_scenarios(self) -> None:
        report = generate_scenario_catalog(PROJECT_ROOT)
        self.assertGreaterEqual(report["scenario_count"], 5)

    def test_final_handoff_is_generated(self) -> None:
        path = generate_final_handoff(PROJECT_ROOT)
        self.assertTrue(path.exists())
        self.assertIn("Final Project Handoff", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
