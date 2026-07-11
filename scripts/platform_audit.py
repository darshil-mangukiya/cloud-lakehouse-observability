from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    "docker-compose.yml",
    "Makefile",
    "requirements.txt",
    "airflow/dags/lakehouse_platform_dag.py",
    "lakehouse/parquet_writer.py",
    "ingestion/api_sources/support_api_client.py",
    "ingestion/api_sources/README.md",
    "spark/jobs/revenue_daily_spark_job.py",
    "spark/README.md",
    "dbt/dbt_project.yml",
    "config/source_registry.json",
    "contracts/source_contracts.json",
    "metadata/schema_registry.json",
    "metadata/data_catalog.json",
    "observability/reports/dataset_readiness.json",
    "observability/reports/slo_report.json",
    "observability/reports/dataset_trust_scores.json",
    "observability/reports/dataset_trust_scores.md",
    "observability/reports/finops/storage_cost_report.json",
    "observability/reports/runtime/runtime_profile.json",
    "observability/reports/parquet_export_manifest.json",
    "data_quality/reports/reconciliation_report.json",
    "metadata/audit_manifest.json",
    "metadata/catalog_validation_report.json",
    "lineage/lineage_graph.json",
    "lineage/lineage_graph.md",
    "security/pii_scan_report.json",
    "semantic_layer/reports/semantic_validation_report.json",
    "security/access_policy_matrix.csv",
    "security/access_policy_matrix.md",
    "operations/replay/backfill_manifest.json",
    "operations/certification/data_product_certification_report.json",
    "operations/certification/data_product_certification_report.md",
    "operations/release/release_gate_report.json",
    "operations/release/release_gate_report.md",
    "operations/exceptions/exception_evaluation_report.json",
    "operations/remediation/remediation_plan.json",
    "operations/remediation/remediation_plan.md",
    "operations/scenarios/scenario_catalog.json",
    "operations/scenarios/scenario_catalog.md",
    "operations/preflight/preflight_report.json",
    "operations/preflight/preflight_report.md",
    "operations/sbom/software_inventory.json",
    "operations/sbom/software_inventory.md",
    "metadata/control_coverage/control_coverage_report.json",
    "metadata/control_coverage/control_coverage_report.md",
    "docs/FINAL_PROJECT_HANDOFF.md",
    "docs/README.md",
    "docs/ingestion_framework.md",
    "docs/data_contracts_and_schema_drift.md",
    "docs/dbt_lakehouse_modeling.md",
    "docs/data_quality_framework.md",
    "docs/observability_and_release_gates.md",
    "docs/metadata_catalog_and_lineage.md",
    "docs/gold_marts_and_kpi_definitions.md",
    "docs/local_setup.md",
    "docs/testing_and_validation.md",
    "docs/troubleshooting_runbook.md",
    "docs/demo_guide.md",
    "docs/dashboard_guide.md",
    "docs/screenshots/README.md",
    "docs/lakehouse_storage_layout.md",
    "docs/cloud_deployment_path.md",
    "dashboards/streamlit/app.py",
    "dashboards/streamlit/README.md",
    "dashboards/streamlit/pages/1_Data_Health.py",
    "dashboards/streamlit/pages/2_Data_Quality.py",
    "dashboards/streamlit/pages/3_Schema_Drift.py",
    "dashboards/streamlit/pages/4_Release_Gates.py",
    "dashboards/streamlit/pages/5_Incidents.py",
    "dashboards/streamlit/pages/6_Gold_Marts.py",
    "dashboards/streamlit/pages/7_Metadata_Lineage.py",
    "dashboards/streamlit/components/loaders.py",
    "dashboards/streamlit/components/cards.py",
    "dashboards/streamlit/components/charts.py",
    "dashboards/streamlit/components/layout.py",
    "dbt/models/marts/dim_customer.sql",
    "dbt/models/marts/dim_product.sql",
    "dbt/models/marts/fact_orders.sql",
    "dbt/models/marts/fact_marketing_spend.sql",
    "observability/reports/scorecards/platform_trust_scorecard.json",
    "observability/reports/scorecards/platform_trust_scorecard.md",
    "alerts/alert_log.jsonl",
    "alerts/notification_outbox.jsonl",
    "lineage/events.jsonl",
    "observability/reports/incidents/latest_incident_summary.md",
    "gold_layer/gold_revenue_analytics.csv",
    "gold_layer/gold_customer_analytics.csv",
    "sample_outputs/sample_data_quality_report.md",
    "sample_outputs/README.md",
    "sample_outputs/sample_schema_drift_event.md",
    "sample_outputs/sample_release_gate_decision.md",
    "sample_outputs/sample_dataset_readiness_report.md",
    "sample_outputs/sample_incident_summary.md",
    "sample_outputs/sample_gold_mart_preview.csv",
    "sample_outputs/sample_lineage_graph.md",
]


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Missing required artifact: {path}")


def main() -> None:
    for relative_path in REQUIRED_PATHS:
        assert_exists(PROJECT_ROOT / relative_path)

    readiness = json.loads((PROJECT_ROOT / "observability/reports/dataset_readiness.json").read_text(encoding="utf-8"))
    if len(readiness) < 8:
        raise AssertionError("Expected at least 8 gold readiness records")

    trust = json.loads((PROJECT_ROOT / "observability/reports/dataset_trust_scores.json").read_text(encoding="utf-8"))
    if trust.get("dataset_count", 0) < 8:
        raise AssertionError("Expected trust scores for all gold datasets")

    parquet_manifest = json.loads((PROJECT_ROOT / "observability/reports/parquet_export_manifest.json").read_text(encoding="utf-8"))
    if parquet_manifest.get("written_count", 0) + parquet_manifest.get("skipped_count", 0) < 8:
        raise AssertionError("Expected Parquet manifest entries for lakehouse datasets")

    events = [line for line in (PROJECT_ROOT / "lineage/events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(events) < 5:
        raise AssertionError("Expected at least 5 lineage events")

    contracts = json.loads((PROJECT_ROOT / "contracts/source_contracts.json").read_text(encoding="utf-8"))
    if len(contracts) < 7:
        raise AssertionError("Expected contracts for all source systems")

    print("Platform audit passed.")


if __name__ == "__main__":
    main()
