from __future__ import annotations

import unittest

from scripts.platform_cli import build_parser


class PlatformCliTests(unittest.TestCase):
    def test_parser_supports_operator_commands(self) -> None:
        parser = build_parser()
        for command in [
            "status",
            "alerts",
            "slos",
            "lineage",
            "catalog",
            "cost",
            "products",
            "semantic",
            "backfill",
            "reconcile",
            "audit",
            "pii",
            "catalog-check",
            "graph",
            "runtime",
            "certify",
            "release",
            "scorecard",
            "exceptions",
            "remediate",
            "coverage",
            "scenarios",
            "handoff",
            "doctor",
            "inventory",
        ]:
            args = parser.parse_args([command])
            self.assertEqual(args.command, command)


if __name__ == "__main__":
    unittest.main()
