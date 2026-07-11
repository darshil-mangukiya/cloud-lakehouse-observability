from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lakehouse.parquet_writer import build_partition_path, write_partitioned_parquet


class ParquetWriterTests(unittest.TestCase):
    def test_partition_path_for_bronze_source(self) -> None:
        path = build_partition_path(
            Path("lakehouse_storage"),
            layer="bronze",
            source_system="ecommerce transactions",
            load_date="2026-05-10",
            batch_id="batch/001",
        )

        self.assertEqual(
            path,
            Path("lakehouse_storage/bronze/source_system=ecommerce_transactions/load_date=2026-05-10/batch_id=batch_001"),
        )

    def test_partition_path_for_gold_dataset(self) -> None:
        path = build_partition_path(
            Path("lakehouse_storage"),
            layer="gold",
            dataset_name="gold_revenue_analytics",
            load_date="2026-05-10",
        )

        self.assertEqual(path, Path("lakehouse_storage/gold/dataset=gold_revenue_analytics/load_date=2026-05-10"))

    def test_writer_returns_written_or_skipped_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_partitioned_parquet(
                [{"order_date": "2026-05-10", "gross_revenue": 100.0}],
                Path(tmp_dir),
                layer="gold",
                dataset_name="gold_revenue_analytics",
                load_date="2026-05-10",
                batch_id="batch_001",
            )

            self.assertIn(result.status, {"written", "skipped"})
            self.assertEqual(result.row_count, 1)
            if result.status == "written":
                self.assertTrue(Path(result.output_path).exists())


if __name__ == "__main__":
    unittest.main()

