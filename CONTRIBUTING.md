# Contributing

This is a portfolio-grade data platform project. Contributions should preserve the production-style structure and the local reproducibility story.

## Local Validation

Before opening a pull request, run:

```bash
python3 -B scripts/local_ci.py
```

This command runs:

1. Full smoke pipeline.
2. Python unit tests.
3. Platform artifact audit.

## Contribution Guidelines

- Keep lakehouse boundaries clear: raw/bronze, silver, and gold should remain separate.
- Prefer metadata-driven controls over one-off scripts.
- Add or update tests when changing ingestion, quality, observability, governance, or release logic.
- Update documentation when adding new operating artifacts or CLI commands.
- Do not commit secrets, credentials, local `.env` files, or generated cache directories.

## Recommended Checks

Useful commands:

```bash
python3 -B scripts/platform_cli.py status
python3 -B scripts/platform_cli.py release
python3 -B scripts/platform_cli.py scorecard
python3 -B scripts/platform_cli.py remediate
python3 -B scripts/platform_cli.py doctor
```
