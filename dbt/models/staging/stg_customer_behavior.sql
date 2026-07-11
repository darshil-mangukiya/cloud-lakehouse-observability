select
    event_id,
    coalesce(customer_id, user_id) as customer_id,
    coalesce(event_ts, event_time)::timestamp as event_ts,
    lower(event_type) as event_type,
    product_id,
    session_id,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'customer_behavior') }}
where event_id is not null
