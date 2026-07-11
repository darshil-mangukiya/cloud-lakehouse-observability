from __future__ import annotations

import unittest
from pathlib import Path

from governance.pii_scanner import run_pii_scan
from lineage.lineage_graph import generate_lineage_graph
from metadata.catalog_validator import validate_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GovernanceValidationTests(unittest.TestCase):
    def test_pii_scan_matches_classification(self) -> None:
        report = run_pii_scan(PROJECT_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertGreater(report["dataset_count"], 1)

    def test_catalog_validation_passes_for_gold_outputs(self) -> None:
        report = validate_catalog(PROJECT_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["missing_gold_catalog_entries"], [])

    def test_lineage_graph_has_nodes_and_edges(self) -> None:
        graph = generate_lineage_graph(PROJECT_ROOT)
        self.assertGreater(graph["node_count"], 1)
        self.assertGreater(graph["edge_count"], 1)


if __name__ == "__main__":
    unittest.main()
