from __future__ import annotations

import unittest
from pathlib import Path

from operations.preflight_checker import run_preflight
from operations.sbom_generator import generate_sbom


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PreflightInventoryTests(unittest.TestCase):
    def test_preflight_has_no_failed_required_checks(self) -> None:
        report = run_preflight(PROJECT_ROOT)
        self.assertEqual(report["failed_count"], 0)
        self.assertIn(report["status"], {"passed", "passed_with_warnings"})

    def test_software_inventory_detects_requirements(self) -> None:
        report = generate_sbom(PROJECT_ROOT)
        self.assertGreater(report["package_count"], 1)
        self.assertGreater(report["dockerfile_count"], 1)


if __name__ == "__main__":
    unittest.main()
