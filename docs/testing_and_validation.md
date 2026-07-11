# Testing And Validation

## Validation Command

```bash
make validate-platform
```

## What It Runs

1. Full local smoke pipeline
2. Python unit tests
3. Platform artifact audit

## Coverage Areas

- source contract validation
- schema registry and drift handling
- quality checks
- dataset trust scoring
- release gate decisions
- alert routing
- incident summary generation
- catalog validation
- lineage graph generation
- governance and security checks
- semantic metric validation

## Why This Matters

The local validation command acts like a CI/CD gate. It proves the project can run end to end and catches regressions in the core platform controls.
