# Lakehouse Architecture

```mermaid
flowchart TB
    subgraph Sources
      Ecom["Ecommerce Transactions"]
      Mkt["Marketing Campaigns"]
      Events["Customer Behavior Logs"]
      Product["Product Catalog"]
      Ops["Operational Logs"]
      Targets["Targets / Planning"]
      CRM["CRM / Support"]
    end

    subgraph Storage["S3 / MinIO Lakehouse Storage"]
      Raw["Raw Landing"]
      Bronze["Bronze<br/>immutable source extracts"]
      Silver["Silver<br/>cleaned and conformed datasets"]
      Gold["Gold<br/>trusted analytical marts"]
      Parquet["Partitioned Parquet Pattern<br/>local optional output"]
    end

    subgraph Control["Platform Control Plane"]
      Registry["Schema Registry"]
      Catalog["Metadata Catalog"]
      Quality["Great Expectations"]
      Observability["Observability Scorecards"]
      Alerts["Alert Store"]
    end

    subgraph Consumers
      BI["Power BI / Tableau / Streamlit"]
      Analysts["Analysts"]
      Execs["Leadership Reporting"]
    end

    Ecom --> Raw
    Mkt --> Raw
    Events --> Raw
    Product --> Raw
    Ops --> Raw
    Targets --> Raw
    CRM --> Raw
    Raw --> Bronze
    Bronze --> Parquet
    Bronze --> Registry
    Bronze --> Silver
    Silver --> Quality
    Silver --> Parquet
    Silver --> Gold
    Gold --> Parquet
    Gold --> BI
    Gold --> Analysts
    Gold --> Execs
    Registry --> Observability
    Quality --> Observability
    Catalog --> Observability
    Observability --> Alerts
```

The design separates data movement from the platform control plane. Data artifacts live in lakehouse layers; operational truth lives in metadata, catalog, quality, observability, and alert tables.

Local lakehouse storage supports CSV/JSON source samples and partitioned Parquet output patterns for cloud-style object storage. The repository also includes one optional PySpark transformation job and one simulated API ingestion source; both are local examples and do not change the core Python/dbt/Docker runtime.
