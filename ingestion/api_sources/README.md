# Simulated API Ingestion Source

This folder contains a local, simulated API ingestion example for support tickets. It demonstrates ingestion behavior beyond static files without requiring external network access.

## What It Demonstrates

- paginated API-style reads
- request metadata capture
- ingestion timestamps
- response validation
- rejected response handling
- bronze landing output

The client uses local mock responses and writes generated runtime data under ignored lakehouse/runtime paths. It is not a live external API integration.

## Run Example

```bash
python3 -B ingestion/api_sources/support_api_client.py --project-root .
```

