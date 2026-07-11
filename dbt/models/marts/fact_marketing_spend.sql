{{ config(materialized='view') }}

select
    campaign_id,
    campaign_date,
    channel,
    spend,
    impressions,
    clicks
from {{ ref('stg_marketing_campaigns') }}

