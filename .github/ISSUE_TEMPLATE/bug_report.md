---
name: Bug report
about: Report a platform, pipeline, quality, or documentation issue
title: "[Bug]: "
labels: bug
assignees: ""
---

## Problem

Describe what failed or behaved unexpectedly.

## Reproduction

```bash
python3 -B scripts/local_ci.py
```

## Expected Behavior

What should have happened?

## Observed Evidence

Attach relevant output from:

- `observability/reports/pipeline_run_summary.json`
- `alerts/alert_log.jsonl`
- `operations/release/release_gate_report.md`
- `operations/remediation/remediation_plan.md`

## Environment

- OS:
- Python version:
- Docker available: yes/no
