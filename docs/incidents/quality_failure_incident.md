# Example Incident: Duplicate Transaction and Missing Customer Key

## Summary

The ecommerce source sent a duplicate transaction and one row with a missing customer ID.

## Detection

- Silver standardization rejected the duplicate primary key.
- Quality validation failed the customer ID null threshold.
- Alerting emitted `rejected_records`, `quality_failure`, and `gold_dataset_not_ready`.

## Impact

`gold_data_quality_summary` was marked at risk. Revenue marts still generated, but data governance would not certify the batch until the source issue was reviewed.

## Follow-Up

- Ask ecommerce engineering to investigate duplicate extract generation.
- Decide whether pending orders without customer ID should be routed to a quarantine flow.
- Add upstream extract idempotency checks.
