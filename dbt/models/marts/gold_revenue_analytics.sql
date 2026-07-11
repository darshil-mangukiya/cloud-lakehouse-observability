{{ config(materialized='incremental', unique_key='order_date') }}

select
    r.order_date,
    r.completed_orders,
    r.gross_revenue,
    r.refund_count,
    r.failed_orders,
    t.revenue_target,
    t.orders_target,
    case when t.revenue_target > 0 then r.gross_revenue / t.revenue_target else 0 end as revenue_attainment
from {{ ref('int_revenue_by_day') }} r
left join {{ ref('stg_targets_planning') }} t
    on r.order_date = t.target_date

{% if is_incremental() %}
where r.order_date >= (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}
