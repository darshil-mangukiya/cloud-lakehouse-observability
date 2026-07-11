select
    p.product_id,
    p.product_name,
    p.category,
    p.active_flag,
    count(*) filter (where o.status = 'completed') as order_count,
    sum(case when o.status = 'completed' then o.quantity else 0 end) as units_sold,
    sum(case when o.status = 'completed' then o.amount else 0 end) as gross_revenue
from {{ ref('stg_product_catalog') }} p
left join {{ ref('stg_ecommerce_transactions') }} o
    on p.product_id = o.product_id
group by 1, 2, 3, 4
