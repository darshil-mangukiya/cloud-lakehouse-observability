{{ config(materialized='view') }}

select
    product_id,
    product_name,
    category,
    active_flag,
    list_price
from {{ ref('stg_product_catalog') }}

