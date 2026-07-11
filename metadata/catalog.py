from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CATALOG_ENTRIES: list[dict[str, Any]] = [
    {
        "dataset_name": "gold_customer_analytics",
        "layer": "gold",
        "owner": "analytics-engineering",
        "source_system": "ecommerce_transactions, customer_behavior, crm_support",
        "refresh_frequency": "daily",
        "criticality_tier": "tier_1",
        "business_description": "Customer-level revenue, engagement, and support health for retention reporting.",
        "downstream_usage": "executive retention dashboards, lifecycle marketing, support leadership",
    },
    {
        "dataset_name": "gold_revenue_analytics",
        "layer": "gold",
        "owner": "finance-analytics",
        "source_system": "ecommerce_transactions, targets_planning",
        "refresh_frequency": "daily",
        "criticality_tier": "tier_1",
        "business_description": "Trusted daily net revenue, order count, refund impact, and target attainment.",
        "downstream_usage": "CFO dashboard, board reporting, revenue operations",
    },
    {
        "dataset_name": "gold_marketing_attribution",
        "layer": "gold",
        "owner": "growth-analytics",
        "source_system": "marketing_campaigns, ecommerce_transactions",
        "refresh_frequency": "daily",
        "criticality_tier": "tier_2",
        "business_description": "Campaign spend, attributed revenue, CAC proxy, and ROAS by channel.",
        "downstream_usage": "marketing performance dashboard, budget planning",
    },
    {
        "dataset_name": "gold_product_performance",
        "layer": "gold",
        "owner": "merchandising-analytics",
        "source_system": "product_catalog, ecommerce_transactions",
        "refresh_frequency": "daily",
        "criticality_tier": "tier_2",
        "business_description": "Product-level orders, revenue, active status, and category performance.",
        "downstream_usage": "category management, assortment planning",
    },
    {
        "dataset_name": "gold_operational_metrics",
        "layer": "gold",
        "owner": "data-platform",
        "source_system": "operational_logs",
        "refresh_frequency": "hourly",
        "criticality_tier": "tier_1",
        "business_description": "Pipeline health, SLA misses, service failures, and operational readiness.",
        "downstream_usage": "data health dashboard, incident review, platform SLO reporting",
    },
    {
        "dataset_name": "gold_target_vs_actual",
        "layer": "gold",
        "owner": "finance-analytics",
        "source_system": "ecommerce_transactions, targets_planning",
        "refresh_frequency": "daily",
        "criticality_tier": "tier_1",
        "business_description": "Daily actual revenue and orders compared with finance planning targets.",
        "downstream_usage": "revenue operations, CFO dashboard, board reporting variance analysis",
    },
    {
        "dataset_name": "gold_data_quality_summary",
        "layer": "gold",
        "owner": "data-governance",
        "source_system": "all validated silver datasets",
        "refresh_frequency": "per pipeline run",
        "criticality_tier": "tier_1",
        "business_description": "Validation outcomes, failed checks, severity, and trendable quality posture.",
        "downstream_usage": "governance scorecards, incident triage",
    },
    {
        "dataset_name": "gold_source_freshness",
        "layer": "gold",
        "owner": "data-platform",
        "source_system": "ingestion metadata",
        "refresh_frequency": "per pipeline run",
        "criticality_tier": "tier_1",
        "business_description": "Source-level load recency, SLA status, row counts, and schema versions.",
        "downstream_usage": "freshness dashboard, alerting, stakeholder trust reporting",
    },
]


def write_catalog(output_dir: Path, runtime_updates: dict[str, dict[str, Any]] | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_updates = runtime_updates or {}
    entries = []
    for entry in CATALOG_ENTRIES:
        merged = dict(entry)
        merged.update(runtime_updates.get(entry["dataset_name"], {}))
        entries.append(merged)
    (output_dir / "data_catalog.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    markdown = ["# Data Catalog", "", "| Dataset | Layer | Owner | Criticality | Description | Downstream Usage |", "|---|---|---|---|---|---|"]
    for entry in entries:
        markdown.append(
            f"| {entry['dataset_name']} | {entry['layer']} | {entry['owner']} | {entry['criticality_tier']} | "
            f"{entry['business_description']} | {entry['downstream_usage']} |"
        )
    (output_dir / "data_catalog.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
