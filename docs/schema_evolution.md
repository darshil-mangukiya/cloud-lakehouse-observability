# Schema Evolution Handling

The platform simulates common production failures:

- Column added: `coupon_code` appears in ecommerce order schema v2.
- Column renamed: `transaction_id` becomes `order_id`; `amount` becomes `order_value`.
- Optional new attributes: campaigns and support sources can introduce new descriptive fields.
- Null explosion: one ecommerce row has a missing customer ID.
- Duplicate records: one transaction ID appears twice in the same source extract.
- Operational failure: quality service emits a failed operational log event.

## Detection

The schema registry infers normalized field names, data types, and nullability for every landed file. It writes:

- current schema fingerprint
- schema version
- drift status
- added columns
- removed columns
- type changes
- safe rename mappings
- breaking flag

## Response

Compatible additive changes and configured safe renames continue through the pipeline. Breaking removals or type changes emit critical alerts and are recorded in drift history. Rejected records are exported separately so the pipeline can continue without hiding data loss.
