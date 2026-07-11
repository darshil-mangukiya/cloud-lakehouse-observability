{{ config(materialized='table') }}

select
    customer_id,
    order_count,
    gross_revenue,
    refund_count,
    last_order_ts,
    behavior_events,
    support_tickets,
    case
        when support_tickets > 0 and refund_count > 0 then 'retention_risk'
        when gross_revenue >= 250 then 'high_value'
        else 'standard'
    end as customer_segment
from {{ ref('int_customer_activity') }}
