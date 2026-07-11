# Backup and Recovery

## Recovery Goals

- Bronze layer is the source of replay truth.
- Metadata tables allow operators to identify the last successful batch.
- Schema registry history explains why a pipeline changed behavior.
- Quality reports and failed records preserve evidence for incident review.

## Backup Targets

- Raw landing and bronze partitions.
- `metadata.load_log`
- `metadata.schema_drift_history`
- `metadata.data_catalog`
- `observability.dataset_readiness`
- `observability.quality_summary`
- `alerts.alert_log`

## Replay Procedure

1. Identify affected batch ID in load log.
2. Restore or locate bronze files for that batch.
3. Re-run silver standardization and quality checks.
4. Rebuild downstream gold marts.
5. Recompute readiness and route alerts if the issue remains.
6. Mark incident resolution status after validation.
