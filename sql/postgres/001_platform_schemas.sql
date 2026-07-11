create schema if not exists raw;
create schema if not exists silver;
create schema if not exists gold;
create schema if not exists metadata;
create schema if not exists observability;
create schema if not exists alerts;

create table if not exists metadata.load_log (
    batch_id text not null,
    source_system text not null,
    load_time timestamptz not null,
    file_name text not null,
    row_count integer not null,
    rejected_count integer not null default 0,
    schema_version integer,
    load_status text not null,
    layer text not null,
    created_at timestamptz not null default now()
);

create table if not exists metadata.schema_drift_history (
    drift_id bigserial primary key,
    source_system text not null,
    previous_version integer,
    current_version integer not null,
    fingerprint text not null,
    status text not null,
    added_columns jsonb not null default '[]',
    removed_columns jsonb not null default '[]',
    type_changes jsonb not null default '{}',
    safe_renames jsonb not null default '{}',
    breaking boolean not null,
    detected_at timestamptz not null default now()
);

create table if not exists metadata.source_contract_validation (
    validation_id bigserial primary key,
    source_system text not null,
    dataset_name text not null,
    validated_at timestamptz not null,
    observed_at timestamptz,
    owner text not null,
    business_domain text,
    business_criticality text,
    criticality_tier text not null,
    schema_compatibility_mode text,
    status text not null,
    outcome text not null,
    row_count integer not null,
    violation_count integer not null,
    observed_columns jsonb not null default '[]',
    expected_columns jsonb not null default '[]',
    safe_renames_applied jsonb not null default '{}',
    violations jsonb not null default '[]',
    downstream_dependencies jsonb not null default '[]',
    created_at timestamptz not null default now()
);

create table if not exists metadata.data_catalog (
    dataset_name text primary key,
    layer text not null,
    owner text not null,
    source_system text not null,
    last_refresh timestamptz,
    schema_version integer,
    business_description text not null,
    downstream_usage text,
    refresh_frequency text,
    criticality_tier text,
    updated_at timestamptz not null default now()
);

create table if not exists metadata.lineage_runs (
    run_id text primary key,
    job_name text not null,
    run_status text not null,
    execution_timestamp timestamptz not null,
    airflow_dag_id text,
    airflow_task_id text,
    dbt_model_name text,
    run_facets jsonb not null default '{}'
);

create table if not exists metadata.lineage_jobs (
    job_name text primary key,
    job_namespace text not null default 'local_lakehouse',
    job_type text not null,
    owner text,
    description text,
    updated_at timestamptz not null default now()
);

create table if not exists metadata.lineage_dataset_edges (
    edge_id bigserial primary key,
    run_id text,
    job_name text not null,
    input_dataset text not null,
    output_dataset text not null,
    transformation_type text not null,
    execution_timestamp timestamptz not null,
    status text not null,
    facets jsonb not null default '{}'
);

create table if not exists metadata.lineage_column_mapping (
    mapping_id bigserial primary key,
    job_name text not null,
    input_dataset text not null,
    input_column text not null,
    output_dataset text not null,
    output_column text not null,
    transformation_rule text,
    updated_at timestamptz not null default now()
);

create table if not exists metadata.downstream_consumers (
    consumer_id bigserial primary key,
    dataset_name text not null,
    consumer_name text not null,
    consumer_type text not null,
    owner text,
    criticality_tier text,
    updated_at timestamptz not null default now()
);

create table if not exists observability.dataset_readiness (
    dataset_name text not null,
    evaluated_at timestamptz not null,
    row_count integer not null,
    quality_status text not null,
    freshness_status text not null,
    schema_status text not null,
    readiness_score numeric(5,4) not null,
    readiness_status text not null,
    primary key (dataset_name, evaluated_at)
);

create table if not exists observability.dataset_trust_scores (
    dataset_name text not null,
    scored_at timestamptz not null,
    trust_score_overall numeric(5,2) not null,
    trust_score_band text not null,
    reason_codes jsonb not null default '[]',
    recommended_action text not null,
    score_components jsonb not null default '[]',
    primary key (dataset_name, scored_at)
);

create table if not exists observability.quality_summary (
    dataset_name text not null,
    validated_at timestamptz not null,
    row_count integer not null,
    check_count integer not null,
    failed_check_count integer not null,
    quality_status text not null,
    details jsonb,
    primary key (dataset_name, validated_at)
);

create table if not exists alerts.alert_log (
    alert_id uuid primary key,
    timestamp timestamptz not null,
    severity text not null,
    alert_type text not null,
    dataset_name text not null,
    source_system text not null,
    business_impact text not null,
    recommended_action text not null,
    resolution_status text not null default 'open',
    resolved_at timestamptz
);

create table if not exists alerts.incidents (
    incident_id uuid primary key,
    severity text not null,
    status text not null,
    affected_dataset text not null,
    affected_source text,
    business_impact text not null,
    detected_at timestamptz not null,
    acknowledged_at timestamptz,
    resolved_at timestamptz,
    root_cause_category text,
    recommended_action text not null,
    assigned_owner text,
    linked_alert_ids jsonb not null default '[]',
    remediation_notes text,
    postmortem_required boolean not null default false
);

create table if not exists alerts.incident_events (
    event_id bigserial primary key,
    incident_id uuid not null references alerts.incidents (incident_id),
    event_timestamp timestamptz not null default now(),
    event_type text not null,
    event_detail text not null,
    actor text not null default 'lakehouse-platform'
);

create table if not exists alerts.remediation_tasks (
    task_id bigserial primary key,
    incident_id uuid references alerts.incidents (incident_id),
    dataset_name text not null,
    assigned_owner text not null,
    recommended_action text not null,
    priority text not null,
    status text not null default 'open',
    due_at timestamptz,
    created_at timestamptz not null default now()
);

create index if not exists idx_load_log_source_time on metadata.load_log (source_system, load_time desc);
create index if not exists idx_alert_log_status_severity on alerts.alert_log (resolution_status, severity, timestamp desc);
create index if not exists idx_readiness_status on observability.dataset_readiness (readiness_status, evaluated_at desc);
create index if not exists idx_contract_validation_status on metadata.source_contract_validation (status, validated_at desc);
create index if not exists idx_lineage_edges_output on metadata.lineage_dataset_edges (output_dataset, execution_timestamp desc);
create index if not exists idx_dataset_trust_band on observability.dataset_trust_scores (trust_score_band, scored_at desc);
create index if not exists idx_incidents_status_severity on alerts.incidents (status, severity, detected_at desc);
