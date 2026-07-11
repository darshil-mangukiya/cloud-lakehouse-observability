# Optional Spark Transformation Example

This folder contains one optional PySpark job for a heavier transformation path. The main platform remains runnable with Python, dbt, Docker, and local files.

## Job

`jobs/revenue_daily_spark_job.py`

The job reads a silver ecommerce orders CSV, aggregates daily completed orders, gross revenue, refunds, and failed orders, then writes a gold-style output partitioned by `order_date`.

## Run Locally

```bash
python3 -B spark/jobs/revenue_daily_spark_job.py \
  --input silver_layer/silver_ecommerce_transactions.csv \
  --output spark_outputs/gold_revenue_daily
```

If PySpark is not installed, the job exits gracefully with a skipped status. This repository does not claim the full platform is Spark-based.

