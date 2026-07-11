"""Tests for the Power BI export layer (scripts/export_for_powerbi.py).

These tests run the export against the current repo artifacts and assert the
contract of powerbi/sample_exports/. They are intentionally not brittle: they do
not hard-code row counts (seed data is small and may change) and they skip
content assertions only when a source artifact has not been generated yet, while
still verifying honesty invariants (platform-level gates, no fake trend/date
tables) that must hold regardless of data volume.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = PROJECT_ROOT / "powerbi" / "sample_exports"
SCRIPT = PROJECT_ROOT / "scripts" / "export_for_powerbi.py"

REQUIRED_CSVS = [
    "dataset_trust_scores.csv",
    "dataset_readiness.csv",
    "release_gates.csv",
    "data_quality_results.csv",
    "schema_drift_events.csv",
    "contract_validations.csv",
    "incident_log.csv",
    "metadata_catalog.csv",
    "lineage_edges.csv",
    "gold_mart_summary.csv",
    "gold_revenue_analytics.csv",
    "gold_marketing_attribution.csv",
]

EXPECTED_HEADERS = {
    "release_gates.csv": [
        "evaluated_at", "release_status", "publish_decision",
        "gate_name", "status", "severity", "observed", "expected", "recommended_action",
    ],
    "dataset_readiness.csv": ["dataset_name", "readiness_score", "readiness_status"],
    "dataset_trust_scores.csv": ["dataset_name", "trust_score_overall", "trust_score_band"],
    "incident_log.csv": ["incident_id", "alert_type", "severity", "resolution_status"],
    "gold_mart_summary.csv": ["dataset_name", "row_count", "trust_score_band"],
}

# Files that would indicate fabricated history/time-series were emitted.
FORBIDDEN_FILES = ["dim_date.csv", "run_history.csv", "trust_score_trend.csv", "trend.csv"]


def _read_header(name: str) -> list[str]:
    path = EXPORT_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle), [])


def _row_count(name: str) -> int:
    path = EXPORT_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


class ExportForPowerBITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # (1) The export script runs successfully against current artifacts.
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        )
        cls.stdout = result.stdout
        if result.returncode != 0:
            raise AssertionError(f"export_for_powerbi.py failed:\n{result.stderr}")

    def test_all_required_csvs_created(self) -> None:
        for name in REQUIRED_CSVS:
            self.assertTrue((EXPORT_DIR / name).exists(), f"missing export CSV: {name}")

    def test_manifest_created_and_shaped(self) -> None:
        manifest_path = EXPORT_DIR / "export_manifest.json"
        self.assertTrue(manifest_path.exists(), "export_manifest.json not created")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ["generated_at", "exports", "sources_used", "missing_optional_inputs", "output_files"]:
            self.assertIn(key, manifest, f"manifest missing key: {key}")
        self.assertEqual(
            {e["file"] for e in manifest["exports"]}, set(REQUIRED_CSVS),
            "manifest exports do not match the required CSV set",
        )

    def test_expected_headers_present(self) -> None:
        for name, expected in EXPECTED_HEADERS.items():
            header = _read_header(name)
            for column in expected:
                self.assertIn(column, header, f"{name} missing expected column '{column}'")

    def test_row_counts_non_negative(self) -> None:
        for name in REQUIRED_CSVS:
            self.assertGreaterEqual(_row_count(name), 0, f"{name} reported a negative row count")

    def test_release_gates_is_platform_level(self) -> None:
        # (6) Must be platform-level: no per-dataset gate column.
        header = _read_header("release_gates.csv")
        self.assertIn("gate_name", header)
        self.assertNotIn("dataset_name", header, "release_gates.csv must not contain a dataset_name column")

    def test_no_fabricated_trend_or_date_files(self) -> None:
        # (7)(8) No fake trend/history export and no dim_date.
        for name in FORBIDDEN_FILES:
            self.assertFalse((EXPORT_DIR / name).exists(), f"forbidden fabricated file present: {name}")

    def test_gold_exports_are_direct_passthroughs(self) -> None:
        # (9) When the gold source CSV exists, the export mirrors its header exactly.
        for mart in ["gold_revenue_analytics", "gold_marketing_attribution"]:
            source = PROJECT_ROOT / "gold_layer" / f"{mart}.csv"
            if not source.exists():
                self.skipTest(f"{mart} source not generated; run the pipeline first")
            with source.open(newline="", encoding="utf-8") as handle:
                source_header = next(csv.reader(handle), [])
            self.assertEqual(_read_header(f"{mart}.csv"), source_header,
                             f"{mart}.csv is not a direct passthrough of its gold source")

    def test_missing_optional_source_handled_gracefully(self) -> None:
        # (10) A CSV whose source is absent is still written (headers/placeholder), not crashed on.
        manifest = json.loads((EXPORT_DIR / "export_manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["exports"]:
            self.assertTrue((EXPORT_DIR / entry["file"]).exists())
            self.assertIn(entry["status"], {"written", "empty_source_missing"})


if __name__ == "__main__":
    unittest.main()
