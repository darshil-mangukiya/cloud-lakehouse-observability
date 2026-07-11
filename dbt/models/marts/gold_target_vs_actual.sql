select
    order_date as target_date,
    gross_revenue as actual_revenue,
    revenue_target,
    completed_orders as actual_orders,
    orders_target,
    revenue_attainment
from {{ ref('gold_revenue_analytics') }}
