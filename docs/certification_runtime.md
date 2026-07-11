# Certification and Runtime Profiling

The platform generates:

- `operations/certification/data_product_certification_report.json`
- `operations/certification/data_product_certification_report.md`
- `observability/reports/runtime/runtime_profile.json`

## Data Product Certification

Certification combines:

- gold dataset readiness
- SLO results
- open critical alerts
- semantic validation
- PII scan status
- catalog validation
- reconciliation status for finance-facing products

Products can be:

- `certified`: no blockers or warnings
- `conditional`: usable with non-blocking warnings
- `blocked`: should not be treated as certified for BI consumption

CLI:

```bash
python3 -B scripts/platform_cli.py certify
```

## Runtime Profile

The runtime profile records duration by major platform phase:

- bronze ingestion
- silver standardization
- quality validation
- gold publication
- reconciliation
- observability scoring
- governance validation

CLI:

```bash
python3 -B scripts/platform_cli.py runtime
```

This gives reviewers a practical operating story: the project can say whether data is trusted and how long each phase took.
