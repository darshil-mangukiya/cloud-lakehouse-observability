# Sample Dataset Readiness Report

| Dataset | Rows | Quality | Freshness | Schema | Readiness | Status |
|---|---:|---|---|---|---:|---|
| `gold_customer_analytics` | 5 | passed | passed | compatible | 1.00 | ready |
| `gold_revenue_analytics` | 2 | passed | passed | compatible | 1.00 | ready |
| `gold_marketing_attribution` | 4 | passed | passed | compatible | 1.00 | ready |
| `gold_product_performance` | 5 | passed | passed | compatible | 1.00 | ready |
| `gold_operational_metrics` | 4 | passed | passed | compatible | 1.00 | ready |
| `gold_target_vs_actual` | 2 | passed | passed | compatible | 1.00 | ready |
| `gold_data_quality_summary` | 7 | failed | passed | compatible | 0.75 | at_risk |
| `gold_source_freshness` | 15 | passed | passed | compatible | 1.00 | ready |

## Interpretation

Readiness combines row presence, quality status, freshness status, and schema compatibility. The platform can publish ready datasets while blocking or flagging datasets that fail operational controls.
