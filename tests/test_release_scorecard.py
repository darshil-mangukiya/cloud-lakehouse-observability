from __future__ import annotations

import unittest
from pathlib import Path

from observability.trust_scorecard import build_trust_scorecard
from operations.release_gate import evaluate_release_gate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReleaseScorecardTests(unittest.TestCase):
    def test_release_gate_has_gates(self) -> None:
        report = evaluate_release_gate(PROJECT_ROOT)
        self.assertGreaterEqual(report["gate_count"], 10)
        self.assertIn(report["release_status"], {"approved", "conditional", "blocked"})

    def test_trust_scorecard_scores_platform(self) -> None:
        report = build_trust_scorecard(PROJECT_ROOT)
        self.assertGreaterEqual(report["trust_score"], 0)
        self.assertLessEqual(report["trust_score"], 100)


if __name__ == "__main__":
    unittest.main()
