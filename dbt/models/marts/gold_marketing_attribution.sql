select
    campaign_id,
    channel,
    spend,
    attributed_orders,
    attributed_revenue,
    case when spend > 0 then attributed_revenue / spend else 0 end as roas
from {{ ref('int_marketing_attribution') }}
