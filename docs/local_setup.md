# Local Setup

## Requirements

- Python 3.10+
- Docker and Docker Compose
- Make
- Optional: dbt CLI for direct dbt commands

## Run The Pipeline

```bash
make run-pipeline
```

## Validate The Platform

```bash
make validate-platform
```

This runs the smoke pipeline, unit tests, and platform artifact audit.

## Start Services

```bash
cp .env.example .env
docker compose up --build
```

The values in `.env.example` are local Docker development defaults only. They are intentionally reproducible placeholders and must be replaced with externally managed secrets and unique credentials outside local development.

## Open Dashboard

```bash
make dashboard
```

## Notes

Generated outputs are ignored by Git. Curated reviewer samples live in `sample_outputs/`.

Dependency ranges favor compatibility for this local portfolio environment. Production release processes should validate and lock exact dependency versions before deployment.
