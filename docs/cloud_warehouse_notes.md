# Cloud Warehouse and Lakehouse Notes

## Snowflake-Style Production Mapping

- Bronze files would land in external stages backed by S3.
- Raw tables can be loaded with Snowpipe or Snowpark jobs.
- dbt models would materialize into `SILVER` and `GOLD` schemas.
- Data quality and observability tables would live in a `PLATFORM_METADATA` database.
- Alerts could route through Snowflake tasks, external functions, or downstream incident tools.

## Databricks-Style Production Mapping

- Bronze, silver, and gold layers map naturally to Delta Lake tables.
- Schema evolution can use Delta expectations and Auto Loader rescued data columns.
- Great Expectations or Delta Live Tables expectations can enforce quality gates.
- Unity Catalog would replace the lightweight metadata catalog for ownership, lineage, access control, and discovery.
- Observability tables can be queried by Databricks SQL dashboards and exported to Prometheus/Grafana if needed.

## Prometheus / Grafana Mapping

- `observability/reports/prometheus_metrics.prom` demonstrates scrape-ready metrics.
- In production, the validator or Airflow task would expose `/metrics`.
- Grafana panels would track readiness score, row counts, failed checks, SLA misses, and open alerts over time.
