from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = PROJECT_ROOT / "dashboards/streamlit"
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.loaders import find_project_root, read_csv_artifact


class StreamlitDashboardTests(unittest.TestCase):
    def test_loader_finds_project_root(self) -> None:
        self.assertEqual(find_project_root(DASHBOARD_ROOT), PROJECT_ROOT)

    def test_missing_artifact_returns_empty_dataframe_with_columns(self) -> None:
        frame = read_csv_artifact("does/not/exist.csv", ["dataset_name", "status"])
        self.assertTrue(frame.empty)
        self.assertEqual(list(frame.columns), ["dataset_name", "status"])

    def test_sample_output_loader_reads_curated_csv(self) -> None:
        frame = read_csv_artifact("sample_outputs/sample_gold_mart_preview.csv")
        self.assertFalse(frame.empty)

    def test_malformed_csv_returns_expected_empty_frame(self) -> None:
        with patch("components.loaders.pd.read_csv", side_effect=pd.errors.ParserError("malformed CSV")):
            frame = read_csv_artifact("sample_outputs/sample_gold_mart_preview.csv", ["dataset_name", "status"])

        self.assertTrue(frame.empty)
        self.assertEqual(list(frame.columns), ["dataset_name", "status"])

    def test_required_dashboard_pages_exist(self) -> None:
        required_paths = [
            DASHBOARD_ROOT / "app.py",
            DASHBOARD_ROOT / "README.md",
            DASHBOARD_ROOT / "components/loaders.py",
            DASHBOARD_ROOT / "pages/1_Data_Health.py",
            DASHBOARD_ROOT / "pages/2_Data_Quality.py",
            DASHBOARD_ROOT / "pages/3_Schema_Drift.py",
            DASHBOARD_ROOT / "pages/4_Release_Gates.py",
            DASHBOARD_ROOT / "pages/5_Incidents.py",
            DASHBOARD_ROOT / "pages/6_Gold_Marts.py",
            DASHBOARD_ROOT / "pages/7_Metadata_Lineage.py",
        ]
        for path in required_paths:
            with self.subTest(path=path):
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
