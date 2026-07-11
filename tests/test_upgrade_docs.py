from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class UpgradeDocsTests(unittest.TestCase):
    def test_screenshot_and_cloud_docs_exist(self) -> None:
        self.assertTrue((PROJECT_ROOT / "docs/screenshots/README.md").exists())
        self.assertTrue((PROJECT_ROOT / "docs/cloud_deployment_path.md").exists())
        self.assertTrue((PROJECT_ROOT / "docs/lakehouse_storage_layout.md").exists())

    def test_gold_mart_docs_include_grain_and_fact_dimension_notes(self) -> None:
        text = (PROJECT_ROOT / "docs/gold_marts_and_kpi_definitions.md").read_text(encoding="utf-8")

        self.assertIn("Grain", text)
        self.assertIn("Fact And Dimension Design Notes", text)
        self.assertIn("fact_orders", text)


if __name__ == "__main__":
    unittest.main()

