# Cloud Deployment Path

This repository is a local Dockerized implementation. The cloud deployment path below is documented as a production extension, not a live deployed environment.

## Storage Mapping

- MinIO/local lakehouse folders map to AWS S3, Google Cloud Storage, or Azure Blob Storage.
- `lakehouse_storage/bronze`, `lakehouse_storage/silver`, and `lakehouse_storage/gold` can map to cloud object prefixes.
- Partitioned Parquet outputs can be copied to cloud object storage without changing the bronze/silver/gold pattern.

## Warehouse And Control Plane

- Local PostgreSQL can map to Amazon RDS, Cloud SQL, Azure Database for PostgreSQL, or a warehouse metadata schema.
- Metadata, alert, observability, lineage, and release-gate tables should live in a managed database with backups and access controls.

## Orchestration

- Local Airflow can map to Amazon MWAA, Cloud Composer, Astronomer, or a managed Kubernetes Airflow deployment.
- DAG environment variables should be managed through secrets and connection backends rather than `.env` files.

## Transformations

- Local dbt can map to dbt Cloud, GitHub Actions, or a managed CI runner.
- dbt profiles should use environment variables or a secrets manager for credentials.

## Runtime Containers

- Docker Compose services can map to ECS, Kubernetes, Cloud Run, or another container platform.
- The validator and dashboard services should be separated from stateful infrastructure in production.

## Production Requirements

- Secrets manager for database, object storage, and Airflow credentials.
- IAM/service accounts scoped to object prefixes and metadata schemas.
- Private networking between orchestration, warehouse, and object storage.
- Centralized logging and metrics export.
- Alert routing to Slack, PagerDuty, email, or an incident system.
- Backup/restore policy for PostgreSQL metadata.
- Retention policy for raw, bronze, silver, gold, and observability artifacts.

