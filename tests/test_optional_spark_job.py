from __future__ import annotations

import unittest

from spark.jobs.revenue_daily_spark_job import pyspark_available


class OptionalSparkJobTests(unittest.TestCase):
    def test_spark_job_imports_without_requiring_pyspark(self) -> None:
        self.assertIsInstance(pyspark_available(), bool)


if __name__ == "__main__":
    unittest.main()

