# Documentation Index

These docs support GitHub review and local execution of the lakehouse platform. Start with the architecture and local setup docs, then review the platform-specific sections as needed.

## Core Docs

| Document | Purpose |
|---|---|
| [architecture.md](architecture.md) | Lakehouse architecture, control plane, and data flow |
| [local_setup.md](local_setup.md) | Local setup and run commands |
| [demo_guide.md](demo_guide.md) | Focused walkthrough of the platform flow |
| [ingestion_framework.md](ingestion_framework.md) | Multi-source ingestion and source onboarding |
| [data_contracts_and_schema_drift.md](data_contracts_and_schema_drift.md) | Source contracts, schema drift, and compatibility handling |
| [dbt_lakehouse_modeling.md](dbt_lakehouse_modeling.md) | dbt staging, intermediate, and mart design |
| [data_quality_framework.md](data_quality_framework.md) | Validation checks and failed-record handling |
| [observability_and_release_gates.md](observability_and_release_gates.md) | Readiness, trust score, incidents, alerts, and release gates |
| [metadata_catalog_and_lineage.md](metadata_catalog_and_lineage.md) | Catalog metadata, ownership, lineage, and downstream usage |
| [gold_marts_and_kpi_definitions.md](gold_marts_and_kpi_definitions.md) | Gold datasets and KPI definitions |
| [dashboard_guide.md](dashboard_guide.md) | Streamlit dashboard guide |
| [screenshots/README.md](screenshots/README.md) | Screenshot capture guide for GitHub visual proof |
| [lakehouse_storage_layout.md](lakehouse_storage_layout.md) | Partitioned Parquet lakehouse layout |
| [cloud_deployment_path.md](cloud_deployment_path.md) | Honest cloud deployment path documentation |
| [testing_and_validation.md](testing_and_validation.md) | Tests, smoke checks, and platform audit |
| [troubleshooting_runbook.md](troubleshooting_runbook.md) | Common operational issues and fixes |

## Supporting Implementation References

These documents describe optional implementation modules that support the platform but are not the main GitHub story.

- [backfill_replay.md](backfill_replay.md)
- [backup_recovery.md](backup_recovery.md)
- [certification_runtime.md](certification_runtime.md)
- [control_coverage_handoff.md](control_coverage_handoff.md)
- [exception_remediation.md](exception_remediation.md)
- [finops.md](finops.md)
- [governance_validation.md](governance_validation.md)
- [operator_cli.md](operator_cli.md)
- [preflight_inventory.md](preflight_inventory.md)
- [production_readiness_review.md](production_readiness_review.md)
- [reconciliation_audit.md](reconciliation_audit.md)
- [schema_evolution.md](schema_evolution.md)
- [security_governance.md](security_governance.md)
- [semantic_layer.md](semantic_layer.md)
- [slo_matrix.md](slo_matrix.md)
- [source_to_target_mapping.md](source_to_target_mapping.md)

## Positioning

This platform makes lakehouse data reliable, observable, governed, and safe for BI consumption.
