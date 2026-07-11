# Source Contracts

`source_contracts.json` defines the operational contract for each source system:

- owner and criticality tier
- business domain and criticality
- primary key
- expected schema and accepted data types
- required and optional columns
- safe rename mappings
- null thresholds and uniqueness rules
- accepted values
- freshness SLA in minutes and hours
- compatibility mode, breaking rules, and non-breaking rules
- quarantine behavior
- downstream gold datasets at risk

The local ingestion runner validates each landed file against these contracts and writes reports to `metadata/contract_reports/`.

Contract outcomes are:

- `PASS`: source load satisfies the contract.
- `WARNING`: non-blocking additive change or review item.
- `FAIL`: contract violation that should block certification or require owner review.
- `QUARANTINE`: breaking or critical violation where affected records/load should not be promoted without remediation.
