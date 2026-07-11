{{ config(materialized='view') }}

select
    transaction_id,
    customer_id,
    product_id,
    campaign_id,
    order_ts,
    order_ts::date as order_date,
    status,
    quantity,
    amount,
    case when status = 'completed' then amount else 0 end as completed_revenue
from {{ ref('stg_ecommerce_transactions') }}

