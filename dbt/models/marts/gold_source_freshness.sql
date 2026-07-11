select
    source_system,
    layer,
    max(load_time) as last_load_time,
    sum(row_count) as row_count,
    max(schema_version) as schema_version,
    case
        when max(load_time) >= now() - interval '24 hours' then 'passed'
        else 'failed'
    end as freshness_status
from {{ source('raw', 'load_log') }}
group by 1, 2
