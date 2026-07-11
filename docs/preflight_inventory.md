# Preflight and Software Inventory

The platform generates:

- `operations/preflight/preflight_report.json`
- `operations/preflight/preflight_report.md`
- `operations/sbom/software_inventory.json`
- `operations/sbom/software_inventory.md`

## Preflight Doctor

The preflight report checks:

- Python runtime version
- required project artifacts
- optional local commands such as Docker, dbt, Airflow, Streamlit, and psql

CLI:

```bash
python3 -B scripts/platform_cli.py doctor
```

## Software Inventory

The software inventory summarizes:

- Python package requirements
- Docker Compose images
- Dockerfiles

CLI:

```bash
python3 -B scripts/platform_cli.py inventory
```

This gives reviewers a quick view of local operability and platform dependencies.
