create table if not exists raw.ecommerce_transactions (
    transaction_id text,
    order_id text,
    customer_id text,
    product_id text,
    order_ts text,
    order_timestamp text,
    amount text,
    order_value text,
    status text,
    quantity text,
    campaign_id text,
    coupon_code text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.marketing_campaigns (
    campaign_id text,
    campaign_date text,
    channel text,
    channel_name text,
    spend text,
    spend_usd text,
    impressions text,
    clicks text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.customer_behavior (
    event_id text,
    customer_id text,
    user_id text,
    event_ts text,
    event_time text,
    event_type text,
    product_id text,
    session_id text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.product_catalog (
    product_id text,
    product_name text,
    category text,
    active_flag text,
    list_price text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.operational_logs (
    log_id text,
    service_name text,
    event_ts text,
    status text,
    runtime_seconds text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.targets_planning (
    target_date text,
    revenue_target text,
    orders_target text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.crm_support (
    ticket_id text,
    customer_id text,
    user_id text,
    created_ts text,
    priority text,
    status text,
    topic text,
    _ingest_batch_id text,
    _source_file text,
    _ingested_at timestamptz
);

create table if not exists raw.data_quality_summary (
    dataset_name text,
    validated_at timestamptz,
    row_count integer,
    check_count integer,
    failed_check_count integer,
    quality_status text
);

create table if not exists raw.load_log (
    source_system text,
    layer text,
    load_time timestamptz,
    row_count integer,
    schema_version integer
);
