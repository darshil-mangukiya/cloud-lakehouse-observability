# Example Incident: Ecommerce Schema Drift

## Summary

The ecommerce source changed `transaction_id` to `order_id`, `amount` to `order_value`, and added `coupon_code`.

## Detection

- Schema registry detected a new fingerprint.
- Source contract validator mapped safe aliases.
- Drift status was recorded as `compatible_evolution`.

## Impact

No downstream outage. Gold revenue, product, marketing, customer, and target datasets remained publishable because aliases were pre-approved.

## Follow-Up

- Update source-to-target mapping with the new optional field.
- Decide whether `coupon_code` should become part of marketing attribution logic.
- Ask upstream source owner to announce future schema changes before deployment.
