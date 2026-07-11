select
    order_ts::date as order_date,
    sum(case when status = 'completed' then 1 else 0 end) as completed_orders,
    sum(case when status = 'completed' then amount else 0 end) as gross_revenue,
    sum(case when status = 'refunded' then 1 else 0 end) as refund_count,
    sum(case when status = 'failed' then 1 else 0 end) as failed_orders
from {{ ref('stg_ecommerce_transactions') }}
group by 1
