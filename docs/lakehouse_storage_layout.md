# Partitioned Parquet Lakehouse Layout

The local pipeline can export bronze, silver, and gold records to partitioned Parquet paths when a Pandas-compatible Parquet engine such as `pyarrow` or `fastparquet` is installed.

Generated Parquet files are intentionally ignored by Git.

## Layout

```text
lakehouse_storage/
  bronze/
    source_system=ecommerce_transactions/
      load_date=YYYY-MM-DD/
        batch_id=<batch_id>/
          part-00000.parquet
  silver/
    dataset=silver_ecommerce_transactions/
      load_date=YYYY-MM-DD/
        batch_id=<batch_id>/
          part-00000.parquet
  gold/
    dataset=gold_revenue_analytics/
      load_date=YYYY-MM-DD/
        batch_id=<batch_id>/
          part-00000.parquet
```

## Manifest

Each pipeline run writes `observability/reports/parquet_export_manifest.json`. If no Parquet engine is installed, the manifest records skipped writes instead of failing the main smoke pipeline.

