# Dashboard Guide

## Purpose

The Streamlit dashboard in `dashboards/streamlit/app.py` is a local data trust command center for reviewing generated P5 platform artifacts. It is not a hosted production dashboard.

Run it with:

```bash
streamlit run dashboards/streamlit/app.py
```

## Pages

### Data Health Command Center

Shows dataset readiness, source health, trust scores, release status, and open alerts.

### Data Quality

Shows validation results, rejected records, failed checks, null breaches, duplicate checks, and row-count anomaly evidence.

### Schema Drift

Shows source-contract outcomes, schema versions, compatible evolution, safe renames, and quarantine signals.

### Release Gates

Shows the platform-level BI publication decision, failed gates, warning gates, and dataset readiness context.

### Alerts And Incidents

Shows alert severity, alert types, open incident context, business impact, and recommended remediation.

### Gold Marts And BI Outputs

Shows generated gold mart inventory, BI readiness, row counts, Parquet output status, and preview tables.

### Metadata And Lineage

Shows catalog ownership, criticality tiers, downstream usage, and source-to-gold lineage.

## Screenshots

Tracked screenshots live in `docs/assets/screenshots/` and are documented in `docs/screenshots/README.md`.

## Reviewer Signal

The dashboard shows that this is an operating platform, not only a transformation project. It gives stakeholders a single place to understand trust, readiness, ownership, and business risk in the local simulated environment.
