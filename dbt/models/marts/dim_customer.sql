{{ config(materialized='view') }}

select
    customer_id,
    customer_segment,
    last_order_ts,
    order_count,
    support_tickets,
    behavior_events
from {{ ref('gold_customer_analytics') }}

