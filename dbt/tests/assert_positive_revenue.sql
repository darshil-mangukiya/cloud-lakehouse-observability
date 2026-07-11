select *
from {{ ref('gold_revenue_analytics') }}
where gross_revenue < 0
