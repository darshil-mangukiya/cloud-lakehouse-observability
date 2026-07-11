# Ingestion Framework

## Simulated API Source

The project includes `ingestion/api_sources/support_api_client.py` as a local simulated API ingestion example. It demonstrates paginated support-ticket reads, request metadata, response validation, rejected response handling, and bronze landing output without requiring an external API.

## Purpose

The ingestion layer lands multiple SaaS/ecommerce source systems into the lakehouse while capturing enough metadata to support schema drift detection, data quality, observability, and replay.

## Sources

- ecommerce transactions
- marketing campaigns
- customer behavior events
- product catalog
- operational logs
- planning and targets
- CRM/support tickets

## Ingestion Responsibilities

| Responsibility | Implementation |
|---|---|
| Source landing | Reads CSV, JSON, and JSONL source files from `raw_data/landing/` |
| Load metadata | Captures batch ID, file name, source system, row count, load time, layer, and schema version |
| Source profiling | Generates source profile summaries for reviewer/debug use |
| Contract validation | Checks source data before promotion |
| Schema registry | Fingerprints schemas and logs drift history |
| Bronze write | Stores immutable source-aligned records with ingestion metadata |
| Rejected records | Routes duplicate, missing-key, and invalid records to failed-record outputs |

## Metadata-Driven Source Registry

`config/source_registry.json` controls source settings such as landing path, primary key, contract path, validation suite, owner, domain, criticality, freshness SLA, retry policy, quarantine behavior, and alerting behavior.

## New Source Onboarding

1. Add the source to `config/source_registry.json`.
2. Add a contract to `contracts/source_contracts.json`.
3. Add source parsing/standardization logic if needed.
4. Add validation checks.
5. Add dbt source/staging/mart logic if it contributes to analytics.
6. Add catalog ownership and downstream usage.
7. Run `make validate-platform`.

## Interview Point

The ingestion layer is designed as a controlled entry point, not a loose file loader. Every source is tied to contracts, metadata, drift detection, and downstream risk.
