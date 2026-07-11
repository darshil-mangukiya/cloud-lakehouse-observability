# Monitoring Dashboards

The Streamlit dashboard reads generated gold exports and observability reports from the local pipeline. The main app lives at `dashboards/streamlit/app.py`.

- Data Health: readiness score, freshness, source health, and dataset status.
- Data Quality: failed checks, null breaches, duplicate issues, and failing datasets.
- Schema Drift: schema registry history and contract outcomes.
- Release Gates: BI publication safety status and blocking reasons.
- Alerts And Incidents: alert history, business impact, and recommended actions.
- Gold Marts: BI-ready marts, fact/dimension views, row counts, and preview tables.
- Metadata And Lineage: catalog metadata, ownership, criticality, downstream usage, and lineage edges.

Run locally:

```bash
make run-pipeline
make dashboard
```

Direct command:

```bash
streamlit run dashboards/streamlit/app.py
```

BI tools can connect to:

- `dashboards/exports/*.csv` for Power BI or Tableau file ingestion.
- PostgreSQL `gold.*`, `observability.*`, `metadata.*`, and `alerts.*` schemas in Docker.
- `observability/reports/prometheus_metrics.prom` for Prometheus-style scraping.
