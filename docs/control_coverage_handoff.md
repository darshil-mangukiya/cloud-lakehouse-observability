# Control Coverage, Scenarios, and Final Handoff

The platform generates:

- `metadata/control_coverage/control_coverage_report.json`
- `metadata/control_coverage/control_coverage_report.md`
- `operations/scenarios/scenario_catalog.json`
- `operations/scenarios/scenario_catalog.md`
- `docs/FINAL_PROJECT_HANDOFF.md`

## Control Coverage

The control coverage report shows which sources and gold datasets are covered by platform controls such as source contracts, schema registry, quality reports, catalog entries, PII classification, SLOs, semantic validation, reconciliation, certification, release gates, and audit manifests.

CLI:

```bash
python3 -B scripts/platform_cli.py coverage
```

## Scenario Catalog

The scenario catalog documents realistic production incidents and which controls should catch them:

- breaking ecommerce schema change
- null explosion in customer identifiers
- late operational logs
- unexpected PII in gold exports
- revenue reconciliation mismatch

CLI:

```bash
python3 -B scripts/platform_cli.py scenarios
```

## Final Handoff

The handoff document gives a reviewer a quick path through the whole project and latest run posture.

CLI:

```bash
python3 -B scripts/platform_cli.py handoff
```
