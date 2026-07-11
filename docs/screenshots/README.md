# Dashboard Screenshot Guide

These screenshots were captured from the local Streamlit observability dashboard after running `make validate-platform`. They show simulated SaaS/ecommerce platform artifacts and do not represent a publicly hosted or production deployment.

| Screenshot | File | Purpose |
| ---------- | ---- | ------- |
| Data Health Command Center | [`data-health-command-center.png`](../assets/screenshots/data-health-command-center.png) | Demonstrates platform health, trust scores, gold dataset readiness, freshness, and the current release decision. |
| Data Quality | [`data-quality.png`](../assets/screenshots/data-quality.png) | Shows validation results, passed and failed checks, rejected records, null breaches, and row-count anomaly evidence. |
| Schema Drift | [`schema-drift.png`](../assets/screenshots/schema-drift.png) | Shows source-contract outcomes, drift events, schema versions, compatible evolution, and quarantine signals. |
| Release Gates | [`release-gates.png`](../assets/screenshots/release-gates.png) | Demonstrates the BI publication control and why an unsafe local release is approved or blocked. |
| Alerts And Incidents | [`alerts-incidents.png`](../assets/screenshots/alerts-incidents.png) | Shows alert severity, incident state, business impact, and recommended remediation actions. |
| Gold Marts And BI Outputs | [`gold-marts-bi-outputs.png`](../assets/screenshots/gold-marts-bi-outputs.png) | Shows reporting mart inventory, BI readiness, row counts, Parquet output status, and preview tables. |
| Metadata And Lineage | [`metadata-lineage.png`](../assets/screenshots/metadata-lineage.png) | Demonstrates catalog ownership, criticality, downstream usage, and source-to-gold lineage. |

## Reproduce The Captures

```bash
make validate-platform
streamlit run dashboards/streamlit/app.py
```

Open `http://localhost:8501`, select each page from the Streamlit sidebar, and capture the visible dashboard at a consistent desktop viewport. The tracked images use `1440x900`.
