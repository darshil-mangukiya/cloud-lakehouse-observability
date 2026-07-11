# Exception and Remediation Workflow

The platform generates:

- `operations/exceptions/exception_evaluation_report.json`
- `operations/remediation/remediation_plan.json`
- `operations/remediation/remediation_plan.md`

## Exception Governance

Exceptions live in `operations/exceptions/exception_register.json`.

Each exception includes:

- exception ID
- owner
- approver
- affected release gate
- reason
- expiration timestamp
- required compensating control

CLI:

```bash
python3 -B scripts/platform_cli.py exceptions
```

## Remediation Plan

The remediation plan converts failed release gates and blocked data products into owner-routed tasks with priorities and due dates.

Priority timing:

- P1: 4 hours
- P2: 24 hours
- P3: 72 hours
- P4: 7 days

CLI:

```bash
python3 -B scripts/platform_cli.py remediate
```

This is the operational bridge between observability and action: a release can be blocked, waived with a controlled exception, or remediated by the right owner.
