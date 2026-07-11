# Sample Release Gate Decision

## Decision

`do_not_publish`

## Reason

The release gate blocks BI publication when a critical quality or contract issue affects a gold dataset.

| Gate | Status | Why It Matters |
|---|---|---|
| silver quality gate | failed | Bad records were detected before gold publication |
| critical alert gate | failed | Open critical data issue requires owner action |
| data product certification | blocked | At least one data product is not safe for business use |
| dataset trust gate | failed | `gold_data_quality_summary` is at risk |
| lineage graph gate | passed | Source-to-gold dependency graph is available |

## Recommended Action

Resolve failed quality checks, review quarantined source records, rerun the pipeline, and publish only after the affected gold dataset returns to a trusted state.
