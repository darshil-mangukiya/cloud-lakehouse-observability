# Operator CLI

The local operator CLI gives quick access to platform state:

```bash
python3 -B scripts/platform_cli.py status
python3 -B scripts/platform_cli.py alerts --open-only
python3 -B scripts/platform_cli.py slos
python3 -B scripts/platform_cli.py lineage
python3 -B scripts/platform_cli.py catalog
python3 -B scripts/platform_cli.py cost
python3 -B scripts/platform_cli.py products
python3 -B scripts/platform_cli.py semantic
python3 -B scripts/platform_cli.py backfill
python3 -B scripts/platform_cli.py reconcile
python3 -B scripts/platform_cli.py audit
python3 -B scripts/platform_cli.py pii
python3 -B scripts/platform_cli.py catalog-check
python3 -B scripts/platform_cli.py graph
python3 -B scripts/platform_cli.py runtime
python3 -B scripts/platform_cli.py certify
python3 -B scripts/platform_cli.py release
python3 -B scripts/platform_cli.py scorecard
python3 -B scripts/platform_cli.py exceptions
python3 -B scripts/platform_cli.py remediate
python3 -B scripts/platform_cli.py coverage
python3 -B scripts/platform_cli.py scenarios
python3 -B scripts/platform_cli.py handoff
python3 -B scripts/platform_cli.py doctor
python3 -B scripts/platform_cli.py inventory
```

This makes the repo feel like an operable platform instead of a folder of disconnected scripts.
