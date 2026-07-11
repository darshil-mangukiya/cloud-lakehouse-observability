# Sample Incident Summary

## Incident

`duplicate transaction spike impacts revenue reporting`

## Severity

`critical`

## Affected Area

- Source: `ecommerce_transactions`
- Silver dataset: `silver_ecommerce_transactions`
- Gold datasets at risk: `gold_revenue_analytics`, `gold_customer_analytics`, `gold_target_vs_actual`

## What Happened

The ingestion layer detected duplicate transaction keys and a customer key completeness issue. The quality framework rejected affected records and generated alerts before the issue reached BI reporting.

## Business Impact

Revenue and customer KPIs may be inaccurate if duplicates are published.

## Recommended Action

Review failed-record exports, confirm source extract behavior, deduplicate upstream or in silver logic, rerun validation, and release only after the gate passes.
