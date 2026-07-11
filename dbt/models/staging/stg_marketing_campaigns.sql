select
    campaign_id,
    campaign_date::date as campaign_date,
    lower(coalesce(channel, channel_name, 'unknown')) as channel,
    {{ safe_cast_numeric("coalesce(spend, spend_usd)") }} as spend,
    impressions::int as impressions,
    clicks::int as clicks,
    _ingest_batch_id,
    _source_file,
    _ingested_at::timestamp as _ingested_at
from {{ source('raw', 'marketing_campaigns') }}
where campaign_id is not null
