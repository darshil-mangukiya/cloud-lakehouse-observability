# Semantic Layer

The semantic layer defines business metrics in `semantic_layer/metrics.yml`.

Included metrics:

- Gross Revenue
- Completed Orders
- Revenue Attainment
- Return on Ad Spend
- Dataset Readiness Score

The pipeline validates that metric expressions resolve against generated gold datasets and observability outputs. Results are written to `semantic_layer/reports/semantic_validation_report.json`.

CLI:

```bash
python3 -B scripts/platform_cli.py semantic
```

In production these definitions could be mapped to dbt Semantic Layer, MetricFlow, LookML, Tableau metrics, or Power BI certified measures.
