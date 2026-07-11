# Governance Validation

The platform generates three additional governance artifacts on every run:

- `security/pii_scan_report.json`
- `metadata/catalog_validation_report.json`
- `lineage/lineage_graph.json` and `lineage/lineage_graph.md`

## PII Classification Scan

The scanner compares detected PII-like columns in silver and gold CSV outputs against `security/data_classification.json`. It flags unexpected customer, user, ticket, session, email, phone, name, or address columns.

CLI:

```bash
python3 -B scripts/platform_cli.py pii
```

## Catalog Completeness

The catalog validator verifies that every generated gold dataset has a catalog entry and that required governance fields are populated:

- owner
- source system
- business description
- downstream usage
- refresh frequency
- criticality tier

CLI:

```bash
python3 -B scripts/platform_cli.py catalog-check
```

## Lineage Graph

The lineage graph turns OpenLineage-style run events into a node/edge graph and a Mermaid diagram. This gives reviewers a quick visual way to understand how source systems, pipeline jobs, and generated datasets relate.

CLI:

```bash
python3 -B scripts/platform_cli.py graph
```
