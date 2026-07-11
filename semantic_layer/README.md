# Semantic Layer

`metrics.yml` documents business metrics on top of gold datasets. This makes the project easier to discuss as an analytics platform, not only a pipeline.

The semantic layer defines:

- metric name and label
- metric type
- source dataset
- expression or ratio inputs
- owner
- business definition
- reusable dimensions

In production, these definitions could map to dbt Semantic Layer, MetricFlow, LookML, Tableau metrics, or Power BI certified measures.
