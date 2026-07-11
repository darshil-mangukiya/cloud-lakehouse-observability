with source as (
    select * from {{ source('raw', 'ecommerce_transactions') }}
),

renamed as (
    select
        coalesce(transaction_id, order_id) as transaction_id,
        customer_id,
        product_id,
        coalesce(order_ts, order_timestamp)::timestamp as order_ts,
        {{ safe_cast_numeric("coalesce(amount, order_value)") }} as amount,
        lower(coalesce(status, 'pending')) as status,
        coalesce(quantity, 1)::int as quantity,
        coalesce(campaign_id, 'unknown') as campaign_id,
        coupon_code,
        _ingest_batch_id,
        _source_file,
        _ingested_at::timestamp as _ingested_at
    from source
)

select *
from renamed
where transaction_id is not null
