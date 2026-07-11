# Gold Marts And KPI Definitions

## Purpose

Gold marts provide stable, BI-ready datasets for analysts and dashboards. The current gold layer uses business-facing marts plus lightweight dbt fact/dimension views for clearer analytics engineering review.

## Gold Mart Details

| Mart | Business Purpose | Grain | Primary Key | Upstream Sources | Key Metrics | Refresh Cadence | BI Use Case | Known Limitations |
|---|---|---|---|---|---|---|---|---|
| `gold_customer_analytics` | Customer value, engagement, support, and retention signals | one row per customer | `customer_id` | `int_customer_activity` | order count, gross revenue, refund count, behavior events, support tickets | daily | retention and customer health reporting | local sample data does not represent full lifecycle history |
| `gold_revenue_analytics` | Daily revenue and target attainment | one row per order date | `order_date` | `int_revenue_by_day`, `stg_targets_planning` | completed orders, gross revenue, refunds, failed orders, revenue attainment | daily | finance and executive revenue reporting | target data exists only for sample dates |
| `gold_marketing_attribution` | Campaign spend and attributed revenue | one row per campaign/channel | `campaign_id`, `channel` | `int_marketing_attribution` | spend, attributed orders, attributed revenue, ROAS | daily | campaign performance and budget review | simple attribution based on campaign id only |
| `gold_product_performance` | Product and category sales performance | one row per product | `product_id` | `int_product_sales` | order count, units sold, gross revenue | daily | product/category performance reporting | no inventory or margin cost table in current sample |
| `gold_operational_metrics` | Platform health and service runtime signals | one row per service | `service_name` | `stg_operational_logs` | event count, failure count, warning count, avg runtime | hourly | data platform health monitoring | based on simulated operational logs |
| `gold_target_vs_actual` | Actual revenue/orders versus planning targets | one row per target date | `target_date` | `gold_revenue_analytics` | actual revenue, target revenue, actual orders, target orders, attainment | daily/monthly target cadence | planning and performance review | depends on available planning rows |
| `gold_data_quality_summary` | Dataset quality posture | one row per validated silver dataset | `dataset_name`, `validated_at` | `raw.data_quality_summary` / validation reports | row count, check count, failed check count, quality status | per pipeline run | quality scorecard and release review | reflects local validation run results |
| `gold_source_freshness` | Source load recency and schema version posture | one row per source/layer load | `source_system`, `layer`, `last_load_time` | `raw.load_log` / metadata load log | row count, schema version, freshness status | per pipeline run | freshness and source health reporting | local timestamps reflect smoke-run execution |

## Lightweight Fact And Dimension Views

| Model | Type | Grain | Purpose |
|---|---|---|---|
| `dim_customer` | dimension view | one row per customer | exposes customer segment and activity attributes from `gold_customer_analytics` |
| `dim_product` | dimension view | one row per product | exposes product name, category, active flag, and list price |
| `fact_orders` | fact view | one row per order/transaction | exposes order-level revenue and dimensional keys |
| `fact_marketing_spend` | fact view | one row per campaign/date | exposes spend, impressions, and clicks |

## Fact And Dimension Design Notes

The primary reporting layer remains BI-ready marts because the project is focused on data reliability, observability, and release control. Lightweight fact/dimension views are included to clarify grain and dimensional thinking without pretending this is a full enterprise star schema. A larger production implementation could separate all marts into conformed facts and dimensions with slowly changing dimensions, but SCD Type 2 is not implemented here.

## Certified KPI Examples

- gross revenue
- completed orders
- revenue attainment
- return on ad spend
- dataset readiness score
- refund count
- failed order count
- units sold
- platform failure count
- source freshness status

## Sample Evidence

See [sample_gold_mart_preview.csv](../sample_outputs/sample_gold_mart_preview.csv).
