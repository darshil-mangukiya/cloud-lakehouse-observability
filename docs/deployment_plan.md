# Deployment Plan

## Local

```bash
make local-ci
make dashboard
```

## Containerized Development

```bash
cp .env.example .env
docker compose up --build
```

## Production Mapping

1. Land source extracts in S3 or managed object storage.
2. Use Airflow or managed orchestration to trigger ingestion.
3. Load raw tables into the warehouse or lakehouse engine.
4. Run dbt models by selector: staging, intermediate, marts.
5. Run Great Expectations checkpoints before certifying gold datasets.
6. Write observability, SLO, lineage, and alert records to platform metadata tables.
7. Publish gold marts to BI tools.

## Promotion Gates

- Source contracts pass.
- dbt build passes.
- Critical Great Expectations checks pass.
- Tier 1 gold readiness score is at least `0.95`.
- No unresolved critical alerts for the batch.
