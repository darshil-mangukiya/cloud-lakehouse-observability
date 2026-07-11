# Data SLO Matrix

| Dataset | Tier | Owner | Freshness SLO | Quality SLO | Readiness SLO |
|---|---|---|---:|---:|---:|
| gold_revenue_analytics | tier_1 | finance-analytics | 24h | 100% critical checks pass | >= 0.95 |
| gold_customer_analytics | tier_1 | analytics-engineering | 24h | 100% critical checks pass | >= 0.95 |
| gold_operational_metrics | tier_1 | data-platform | 1h | 100% critical checks pass | >= 0.95 |
| gold_data_quality_summary | tier_1 | data-governance | 1h | 100% critical checks pass | >= 0.95 |
| gold_source_freshness | tier_1 | data-platform | 1h | 100% critical checks pass | >= 0.95 |
| gold_marketing_attribution | tier_2 | growth-analytics | 24h | 95% non-critical checks pass | >= 0.90 |
| gold_product_performance | tier_2 | merchandising-analytics | 24h | 95% non-critical checks pass | >= 0.90 |

Tier 1 failures should generate a critical alert and require owner acknowledgement before downstream dashboards are certified.
