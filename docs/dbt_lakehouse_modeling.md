# dbt Lakehouse Modeling

## Purpose

The project uses dbt to model lakehouse data into analytics-ready datasets.

## Layers

| Layer | Role |
|---|---|
| Bronze | Raw source-aligned data and ingestion metadata |
| Silver | Standardized, typed, deduplicated, quality-checked data |
| Gold | BI-ready marts and KPI datasets |

## dbt Structure

- `dbt/models/staging`: source conformance and type-safe staging models
- `dbt/models/intermediate`: reusable joins and business logic
- `dbt/models/marts`: trusted gold models
- `dbt/macros`: reusable SQL helpers
- `dbt/tests`: custom data tests
- `dbt/seeds`: small governed reference data

## Gold Marts

The gold layer includes revenue, customer, marketing, product, operations, target-vs-actual, quality, and freshness datasets.

## Interview Point

The marts are business-facing, not source-shaped. Analysts query stable gold datasets instead of rebuilding logic from raw extracts.
