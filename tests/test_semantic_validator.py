from __future__ import annotations

import unittest
from pathlib import Path

from semantic_layer.semantic_validator import validate_semantic_layer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SemanticValidatorTests(unittest.TestCase):
    def test_semantic_metrics_resolve_against_generated_outputs(self) -> None:
        report = validate_semantic_layer(PROJECT_ROOT)
        self.assertEqual(report["status"], "passed")
        self.assertGreaterEqual(report["metric_count"], 5)


if __name__ == "__main__":
    unittest.main()
