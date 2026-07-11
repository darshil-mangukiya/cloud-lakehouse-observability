select
    log_id,
    service_name,
    event_ts::timestamp as event_ts,
    lower(status) as status,
    runtime_seconds::int as runtime_seconds,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'operational_logs') }}
where log_id is not null
