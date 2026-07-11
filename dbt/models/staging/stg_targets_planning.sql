select
    target_date::date as target_date,
    {{ safe_cast_numeric("revenue_target") }} as revenue_target,
    orders_target::int as orders_target,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'targets_planning') }}
where target_date is not null
