# FinOps and Storage Reporting

The platform generates `observability/reports/finops/storage_cost_report.json` on every smoke run.

It reports:

- file count by layer
- storage size by layer
- total storage footprint
- estimated S3 Standard storage cost

This is intentionally simple, but it demonstrates that a data platform should expose cost and usage signals alongside freshness and quality. In production this would be extended with object storage request counts, warehouse/dbt compute cost, Airflow runtime, and dashboard query usage.

CLI:

```bash
python3 -B scripts/platform_cli.py cost
```
