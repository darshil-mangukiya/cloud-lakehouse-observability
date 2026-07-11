select
    ticket_id,
    coalesce(customer_id, user_id) as customer_id,
    created_ts::timestamp as created_ts,
    lower(priority) as priority,
    lower(status) as status,
    topic,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'crm_support') }}
where ticket_id is not null
