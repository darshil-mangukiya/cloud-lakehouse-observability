# Production Readiness Review

## Reliability Controls

- Source contracts define required fields, primary keys, safe renames, accepted values, owners, criticality, and downstream blast radius.
- Schema registry fingerprints each landed file and records compatible evolution versus breaking drift.
- Silver validation catches duplicates, null threshold breaches, invalid accepted values, and non-negative metric violations.
- Gold readiness combines row availability, quality status, freshness status, and schema status.
- Alerts include business impact and recommended action so failures are actionable, not just technical noise.

## Operational Controls

- Airflow DAG uses task groups for ingestion, bronze-to-silver, validation, silver-to-gold, exports, and alerts.
- PostgreSQL schemas separate raw, silver, gold, metadata, observability, and alert domains.
- OpenLineage-style events are written to `lineage/events.jsonl` for run-level lineage and auditability.
- Generated incident summaries provide a human-readable operating view for open alerts and gold datasets at risk.
- The platform CLI lets operators inspect status, alerts, SLOs, lineage, and catalog state without opening every artifact manually.
- Docker Compose provides a reproducible local platform stack.
- Terraform scaffolds the production lakehouse bucket with encryption and versioning.

## Governance Controls

- Data catalog captures ownership, descriptions, criticality, refresh frequency, and downstream usage.
- Source-to-target mapping documents how raw fields become trusted marts.
- Runbooks cover pipeline failures, schema drift, quality failures, and gold readiness incidents.
- Critical dataset tiers are available as a dbt seed for future SLO joins.
- Data products and semantic metrics document the business-facing contract of the gold layer.

## Known Local Simulation Boundaries

- The local pipeline writes JSONL/CSV lakehouse artifacts; Dockerized PostgreSQL loading is available through `ingestion/postgres_loader.py`.
- Alerting writes to JSONL by default and can also write to PostgreSQL when `ALERT_POSTGRES_DSN` is set.
- Great Expectations suites are included; the local smoke path uses a dependency-light validator so tests run without a heavy service bootstrap.
