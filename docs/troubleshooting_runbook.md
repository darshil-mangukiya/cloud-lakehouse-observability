# Troubleshooting Runbook

## Contract Failure

1. Open the source contract report.
2. Check missing columns, type changes, duplicate keys, null thresholds, and freshness.
3. Confirm whether the change is expected with the source owner.
4. Update source mapping or contract only after business approval.
5. Rerun `make validate-platform`.

## Schema Drift

1. Review schema registry history.
2. Identify whether the change is additive, renamed, removed, or type changed.
3. For safe renames, update alias mappings.
4. For breaking drift, quarantine and update dbt/staging logic.

## Quality Failure

1. Inspect failed-record exports.
2. Identify duplicate, null, accepted value, or type violations.
3. Fix upstream source data or silver standardization logic.
4. Rerun validation and release gate.

## Release Blocked

1. Open the release gate report.
2. Triage failed critical gates first.
3. Review dataset trust reason codes.
4. Resolve incidents or document an exception.
5. Publish only after the gate returns approved or explicitly conditional.
