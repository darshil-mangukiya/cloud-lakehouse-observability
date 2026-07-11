# Demo Guide

## Goal

Show how the platform prevents unreliable data from reaching BI reporting.

## Demo Script

1. Run the validation gate.

```bash
make validate-platform
```

2. Explain that source files include realistic issues: schema renames, duplicate transactions, missing customer keys, and optional new fields.

3. Open the data contract example.

```bash
contracts/source_contracts.json
```

4. Show the schema drift sample.

```bash
sample_outputs/sample_schema_drift_event.md
```

5. Show the failed quality sample.

```bash
sample_outputs/sample_data_quality_report.md
```

6. Show the readiness and trust story.

```bash
sample_outputs/sample_dataset_readiness_report.md
```

7. Show the release decision.

```bash
sample_outputs/sample_release_gate_decision.md
```

8. Open the dashboard.

```bash
make dashboard
```

## Talk Track

The key story is simple: source issues are detected early, bad records are contained, trusted records become gold marts, and the release gate prevents unsafe datasets from being published to BI.
