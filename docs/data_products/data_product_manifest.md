# Data Product Manifest

Gold datasets are treated as certified data products with ownership, SLAs, quality expectations, trust thresholds, consumers, metric definitions, access classification, and known limitations.

| Data Product | Owner | Domain | Tier | Datasets | Trust Threshold | Certification |
|---|---|---|---|---|---:|---|
| Revenue Intelligence | finance-analytics | finance | tier_1 | `gold_revenue_analytics`, `gold_target_vs_actual` | 90 | conditional |
| Customer Health | analytics-engineering | customer | tier_1 | `gold_customer_analytics` | 90 | certified |
| Growth Performance | growth-analytics | marketing | tier_2 | `gold_marketing_attribution` | 80 | certified |
| Platform Reliability | data-platform | platform_operations | tier_1 | `gold_operational_metrics`, `gold_data_quality_summary`, `gold_source_freshness` | 90 | conditional |

## Certification Inputs

Certification checks include:

- dataset readiness
- source freshness SLOs
- dataset trust score
- semantic validation
- PII scan status
- catalog completeness
- reconciliation status where financial metrics are involved
- open alerts and incidents

## Governance Metadata

Each product records:

- source of truth status
- refresh cadence
- downstream consumers
- metric definitions
- access classification
- PII classification
- last certification date
- known limitations

This lets the project show gold marts as governed products, not only SQL outputs.
