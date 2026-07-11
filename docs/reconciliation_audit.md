# Reconciliation and Auditability

The platform now generates two audit-oriented artifacts:

- `data_quality/reports/reconciliation_report.json`
- `metadata/audit_manifest.json`

## Reconciliation

The reconciliation report verifies that key gold metrics tie back to silver source-of-truth datasets:

- completed ecommerce revenue equals gold revenue
- completed order count equals gold revenue order count
- product revenue equals completed ecommerce revenue
- target-vs-actual revenue equals gold revenue

CLI:

```bash
python3 -B scripts/platform_cli.py reconcile
```

## Audit Manifest

The audit manifest records artifact path, byte size, row count where applicable, and SHA-256 checksum for generated silver, gold, metadata, observability, alert, lineage, semantic, security, and replay artifacts.

CLI:

```bash
python3 -B scripts/platform_cli.py audit
```

This gives the project a defensible control story: operators can prove what was produced, when it was produced, how large it was, and whether key totals reconcile.
