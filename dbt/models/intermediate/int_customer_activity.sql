with orders as (
    select
        customer_id,
        count(*) as order_count,
        sum(case when status = 'completed' then amount else 0 end) as gross_revenue,
        sum(case when status = 'refunded' then 1 else 0 end) as refund_count,
        max(order_ts) as last_order_ts
    from {{ ref('stg_ecommerce_transactions') }}
    group by 1
),

events as (
    select customer_id, count(*) as behavior_events
    from {{ ref('stg_customer_behavior') }}
    group by 1
),

support as (
    select customer_id, count(*) as support_tickets
    from {{ ref('stg_crm_support') }}
    group by 1
)

select
    coalesce(orders.customer_id, events.customer_id, support.customer_id) as customer_id,
    coalesce(order_count, 0) as order_count,
    coalesce(gross_revenue, 0) as gross_revenue,
    coalesce(refund_count, 0) as refund_count,
    last_order_ts,
    coalesce(behavior_events, 0) as behavior_events,
    coalesce(support_tickets, 0) as support_tickets
from orders
full outer join events using (customer_id)
full outer join support using (customer_id)
