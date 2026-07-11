from __future__ import annotations

from collections import Counter
from typing import Any

from ingestion.schema_registry import normalize_column_name


def profile_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = len(records)
    columns = sorted({normalize_column_name(key) for record in records for key in record})
    null_counts = {column: 0 for column in columns}
    distinct_values: dict[str, set[str]] = {column: set() for column in columns}
    duplicate_counter: Counter[str] = Counter()

    for record in records:
        canonical = {}
        for key, value in record.items():
            canonical[normalize_column_name(key)] = value
        duplicate_counter.update([repr(sorted(canonical.items()))])
        for column in columns:
            value = canonical.get(column)
            if value in (None, ""):
                null_counts[column] += 1
            else:
                distinct_values[column].add(str(value))

    duplicate_rows = sum(count - 1 for count in duplicate_counter.values() if count > 1)
    null_rates = {
        column: (null_counts[column] / row_count if row_count else 0.0)
        for column in columns
    }
    return {
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "null_counts": null_counts,
        "null_rates": null_rates,
        "distinct_counts": {column: len(values) for column, values in distinct_values.items()},
        "duplicate_rows": duplicate_rows,
        "duplicate_rate": duplicate_rows / row_count if row_count else 0.0,
    }
