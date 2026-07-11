# Security and Governance

## Data Classification

Classification metadata lives in `security/data_classification.json` and assigns datasets to:

- `public`: safe for broad internal visibility.
- `confidential`: business-sensitive metrics or operational data.
- `restricted`: customer identifiers, support context, or customer-level behavioral data.

## Access Model

- Raw and bronze data should be limited to the data platform team.
- Silver data should be available to analytics engineers and approved domain owners.
- Gold data should be the default interface for BI consumers.
- Restricted datasets should require purpose-based access and audit logging.

## Controls

- Keep immutable bronze files for replay and auditability.
- Use gold marts for governed reporting instead of ad hoc source extracts.
- Record ownership, criticality, downstream usage, and refresh expectations in the catalog.
- Route critical alerts to incident channels and require resolution status tracking.
- Apply encryption and versioning to production object storage.

## PII Handling

Customer identifiers are retained in local samples for portfolio clarity. In production, this project would add tokenization or hashed identifiers in gold marts where direct customer IDs are not required.
