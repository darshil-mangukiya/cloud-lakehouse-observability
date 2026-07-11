select
    service_name,
    count(*) as event_count,
    count(*) filter (where status = 'failed') as failure_count,
    count(*) filter (where status = 'warning') as warning_count,
    avg(runtime_seconds) as avg_runtime_seconds,
    max(event_ts) as last_event_ts
from {{ ref('stg_operational_logs') }}
group by 1
