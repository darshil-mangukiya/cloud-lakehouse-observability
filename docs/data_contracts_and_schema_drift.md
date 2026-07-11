# Data Contracts And Schema Drift

## Purpose

Contracts and schema drift handling prevent upstream changes from silently breaking silver models, gold marts, and dashboards.

## What Is Implemented

- Source contracts in `contracts/source_contracts.json`
- Contract validator in `ingestion/contract_validator.py`
- Schema fingerprinting and drift detection in `ingestion/schema_registry.py`
- Safe rename mappings for known source changes
- Outcomes: `PASS`, `WARNING`, `FAIL`, `QUARANTINE`
- Contract reports generated under `metadata/contract_reports/`

## Contract Checks

| Check | Example |
|---|---|
| Required columns | `transaction_id`, `customer_id`, `amount` |
| Type compatibility | `amount` must remain numeric-compatible |
| Null thresholds | customer key null spike is blocked |
| Primary key uniqueness | duplicate transaction IDs are rejected |
| Accepted values | order status must use known values |
| Freshness SLA | stale source files fail validation |

## Schema Evolution Policy

| Change | Handling |
|---|---|
| approved rename | allowed and logged |
| optional column added | allowed as compatible evolution |
| required column removed | fail or quarantine |
| type changed | fail or quarantine |
| null explosion | fail or quarantine based on source criticality |

## Interview Point

The platform does not wait for dashboards to break. It checks source contracts and schema compatibility before data is promoted.
