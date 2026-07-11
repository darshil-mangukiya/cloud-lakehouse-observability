select
    coalesce(o.campaign_id, 'unknown') as campaign_id,
    coalesce(m.channel, 'unknown') as channel,
    coalesce(max(m.spend), 0) as spend,
    count(*) filter (where o.status = 'completed') as attributed_orders,
    sum(case when o.status = 'completed' then o.amount else 0 end) as attributed_revenue
from {{ ref('stg_ecommerce_transactions') }} o
left join {{ ref('stg_marketing_campaigns') }} m
    on o.campaign_id = m.campaign_id
group by 1, 2
