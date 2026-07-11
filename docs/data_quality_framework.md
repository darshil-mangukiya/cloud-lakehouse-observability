# Data Quality Framework

## Purpose

The data quality layer prevents incomplete, duplicated, invalid, or unstable data from reaching gold reporting datasets.

## What Is Implemented

- Great Expectations-style validation runner
- Schema checks
- Null thresholds
- Duplicate and uniqueness checks
- Accepted value constraints
- Row count and anomaly signals
- Failed record exports
- Reconciliation checks for gold outputs

## Quality Flow

1. Source files land in raw/bronze.
2. Contracts validate source shape and critical rules.
3. Silver standardization cleans and deduplicates records.
4. Validation checks run against silver datasets.
5. Failed checks reduce readiness and can block release.

## Sample Evidence

See [sample_data_quality_report.md](../sample_outputs/sample_data_quality_report.md).

## Interview Point

Quality checks are treated as publish controls, not passive reports.
