# Sample Data Quality Report

## Dataset

`silver_ecommerce_transactions`

## Purpose

Demonstrates that the platform catches realistic data quality issues before they reach gold marts.

## Example Result

| Check | Status | Observed | Expected | Business Impact |
|---|---|---:|---|---|
| primary key uniqueness | failed | duplicate transaction ID | unique `transaction_id` | Revenue can be double counted |
| customer key completeness | failed | missing `customer_id` | null ratio <= 5% | Customer analytics can become incomplete |
| accepted order status | passed | completed, refunded, failed | known status values | KPI grouping is stable |
| amount type and sign | passed | positive decimals | numeric amount >= 0 | Revenue metrics are safe to aggregate |

## Platform Response

- Bad records are written to failed-record exports.
- Contract and quality alerts are emitted.
- Dataset readiness is reduced.
- Release gate blocks unsafe publication when critical checks fail.
