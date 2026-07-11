from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def pyspark_available() -> bool:
    try:
        import pyspark  # noqa: F401
    except ImportError:
        return False
    return True


def run_job(input_path: Path, output_path: Path) -> dict[str, Any]:
    if not pyspark_available():
        return {
            "status": "skipped",
            "reason": "pyspark is not installed",
            "input_path": str(input_path),
            "output_path": str(output_path),
        }

    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = SparkSession.builder.appName("lakehouse-revenue-daily").getOrCreate()
    try:
        orders = spark.read.option("header", True).csv(str(input_path))
        required_columns = {"transaction_id", "order_ts", "amount", "status"}
        missing = sorted(required_columns - set(orders.columns))
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        daily = (
            orders.withColumn("order_date", F.to_date("order_ts"))
            .withColumn("amount_numeric", F.col("amount").cast("double"))
            .groupBy("order_date")
            .agg(
                F.sum(F.when(F.col("status") == "completed", 1).otherwise(0)).alias("completed_orders"),
                F.sum(F.when(F.col("status") == "completed", F.col("amount_numeric")).otherwise(0.0)).alias("gross_revenue"),
                F.sum(F.when(F.col("status") == "refunded", 1).otherwise(0)).alias("refund_count"),
                F.sum(F.when(F.col("status") == "failed", 1).otherwise(0)).alias("failed_orders"),
            )
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        daily.write.mode("overwrite").partitionBy("order_date").parquet(str(output_path))
        return {
            "status": "written",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "row_count": daily.count(),
        }
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional PySpark daily revenue aggregation.")
    parser.add_argument("--input", default="silver_layer/silver_ecommerce_transactions.csv")
    parser.add_argument("--output", default="spark_outputs/gold_revenue_daily")
    args = parser.parse_args()
    result = run_job(Path(args.input), Path(args.output))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

