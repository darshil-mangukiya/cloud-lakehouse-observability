# Sample Schema Drift Event

## Source

`ecommerce_transactions`

## Event

The source changed order fields while adding a new optional marketing field.

| Change | Example | Compatibility |
|---|---|---|
| renamed column | `order_id` -> `transaction_id` | compatible through approved alias |
| renamed column | `order_value` -> `amount` | compatible through approved alias |
| renamed column | `order_timestamp` -> `order_ts` | compatible through approved alias |
| added column | `coupon_code` | non-breaking optional column |
| null spike | `customer_id` null ratio exceeded threshold | contract violation |

## Platform Response

- Schema registry creates a new schema version.
- Approved renames are mapped safely.
- Optional additive change is allowed.
- Critical null threshold breach produces `QUARANTINE`.
- Downstream gold datasets are marked at risk until remediation.
