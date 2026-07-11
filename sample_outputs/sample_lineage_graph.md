# Sample Lineage Graph

```mermaid
flowchart LR
    Orders["ecommerce_transactions source"]
    Campaigns["marketing_campaigns source"]
    Behavior["customer_behavior source"]
    Products["product_catalog source"]
    Bronze["bronze raw lake"]
    Silver["silver standardized datasets"]
    DBT["dbt staging + intermediate models"]
    Revenue["gold_revenue_analytics"]
    Marketing["gold_marketing_attribution"]
    Customer["gold_customer_analytics"]
    Dashboard["BI dashboard / Streamlit command center"]

    Orders --> Bronze --> Silver --> DBT
    Campaigns --> Bronze
    Behavior --> Bronze
    Products --> Bronze
    DBT --> Revenue --> Dashboard
    DBT --> Marketing --> Dashboard
    DBT --> Customer --> Dashboard
```

## Blast Radius Example

If `ecommerce_transactions` fails contract validation, revenue, customer, product, marketing attribution, and target-vs-actual marts are all considered at risk.
