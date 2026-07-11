select
    product_id,
    product_name,
    category,
    active_flag::boolean as active_flag,
    {{ safe_cast_numeric("list_price") }} as list_price,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'product_catalog') }}
where product_id is not null
