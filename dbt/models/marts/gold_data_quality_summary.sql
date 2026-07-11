select
    dataset_name,
    validated_at,
    row_count,
    check_count,
    failed_check_count,
    quality_status
from {{ source('raw', 'data_quality_summary') }}
