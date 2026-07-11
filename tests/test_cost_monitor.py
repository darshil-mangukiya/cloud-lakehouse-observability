from __future__ import annotations

import unittest
from pathlib import Path

from observability.cost_monitor import generate_cost_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CostMonitorTests(unittest.TestCase):
    def test_cost_report_includes_lakehouse_layers(self) -> None:
        report = generate_cost_report(PROJECT_ROOT)
        layers = {row["layer"] for row in report["layers"]}
        self.assertIn("bronze", layers)
        self.assertIn("silver", layers)
        self.assertIn("gold", layers)


if __name__ == "__main__":
    unittest.main()
