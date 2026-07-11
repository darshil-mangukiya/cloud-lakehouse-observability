# Source-to-Target Mapping

| Source | Bronze | Silver | Gold Consumers |
|---|---|---|---|
| ecommerce_transactions | raw order extracts with schema metadata | `silver_ecommerce_transactions` | revenue, customer, marketing, product, target vs actual |
| marketing_campaigns | campaign performance files | `silver_marketing_campaigns` | marketing attribution |
| customer_behavior | JSONL event stream | `silver_customer_behavior` | customer analytics |
| product_catalog | product reference data | `silver_product_catalog` | product performance |
| operational_logs | platform service logs | `silver_operational_logs` | operational metrics, system dashboard |
| targets_planning | revenue and order targets | `silver_targets_planning` | target vs actual, revenue analytics |
| crm_support | support tickets | `silver_crm_support` | customer analytics |

## Important Transform Rules

- `order_id` maps to `transaction_id`.
- `order_value` maps to `amount`.
- `order_timestamp` maps to `order_ts`.
- `user_id` maps to `customer_id`.
- `spend_usd` maps to `spend`.
- Primary keys are deduplicated in silver.
- Invalid keys and duplicate records are exported to failed record files.
