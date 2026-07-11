# P5 Trusted Business Reporting & Data Readiness Dashboard (Power BI)

This Power BI dashboard is a **downstream BI consumption layer** built from P5's
generated gold outputs and observability exports. It demonstrates how trust-scored
datasets can support business reporting **after** release-gate evaluation.

> Streamlit remains the platform observability dashboard. Power BI demonstrates
> how generated lakehouse outputs can support trusted business reporting after
> release-gate evaluation.

Streamlit stays engineer-facing and live; Power BI shows how the same generated
gold marts can feed business reporting, with a trust / readiness overlay on
every business view.

## Why this exists (and how it differs from Streamlit)

| | Streamlit (`dashboards/streamlit/`) | Power BI (this folder) |
|---|---|---|
| Audience | Platform / data engineers | BI consumers, analytics & BI managers |
| Reads from | Live runtime JSON artifacts | Flat CSV exports (`sample_exports/`) |
| Focus | Operating the lakehouse platform | Trusted **business reporting** + readiness proof |
| Differentiator | Full observability console | Gold business metrics **gated by** trust / release status |

It is intentionally **not** a sales dashboard. Business metrics appear only with
their dataset's trust score, readiness status, and release-gate decision attached.

## How to regenerate the sample exports

The CSVs in `sample_exports/` are produced from real platform artifacts — nothing
is hand-authored or fabricated.

```bash
# 1. Generate the platform artifacts (one clean run)
python pipelines/run_platform.py --reset

# 2. Flatten them into Power BI CSVs
python scripts/export_for_powerbi.py
```

`scripts/export_for_powerbi.py` reads existing reports (observability, quality,
release gate, schema registry, alerts, catalog, lineage, gold marts) and writes
flat CSVs plus `export_manifest.json`. If a source artifact is missing it writes a
documented placeholder and marks it `empty_source_missing` rather than inventing
data — so always run the pipeline first.

## How to build the Power BI file

1. Open Power BI Desktop → **Get Data → Text/CSV** → load all files from `sample_exports/`.
2. Model relationships (single-direction, `dim_dataset[dataset_name]` is optional):
   - `dataset_trust_scores[dataset_name]` ↔ `dataset_readiness[dataset_name]` ↔ `gold_mart_summary[dataset_name]`
   - `data_quality_results[dataset_name]`, `incident_log[dataset_name]`, `metadata_catalog[dataset_name]` relate on `dataset_name`
   - `schema_drift_events` / `contract_validations` relate on `source_system`
   - `release_gates` is platform-level (gate grain) — keep it as a standalone table, do **not** force a per-dataset relationship.
3. Build the 5 pages (below), save as `P5_Lakehouse_Data_Trust_Observability.pbix` here.
4. Capture the 5 screenshots into `screenshots/` (names listed below).

## The 5 pages

1. **Executive Data Trust Overview** — point-in-time only (no trend charts; there is
   no multi-run history). Cards: Overall Trust Score, Avg Readiness, BI-Ready Datasets,
   At-Risk/Blocked, Failed Quality Checks, Open Incidents, and Gold Marts Generated.
   Visuals: readiness by dataset, release-gate status donut, top-risk datasets table.
2. **Trusted Business Reporting** — the differentiator. Business metrics from
   `gold_revenue_analytics` and `gold_marketing_attribution`, each visual annotated with
   trust band + readiness + gate status via `gold_mart_summary`.
3. **Data Quality & Schema Drift** — `data_quality_results` (passed vs failed by dataset
   and rule type) + `schema_drift_events` / `contract_validations`.
4. **Release Gates & BI Readiness** — `release_gates` (12 platform gates, with the overall
   `release_status` / `publish_decision`) + `dataset_readiness` per-dataset breakdown.
5. **Incidents, Lineage & Metadata** — `incident_log`, `metadata_catalog`, and a
   `lineage_edges` source→bronze→silver→gold→output table.

## Suggested base measures (keep DAX light — these live in the .pbix)

```DAX
Overall Trust Score = AVERAGE(dataset_trust_scores[trust_score_overall])
Average Readiness Score = AVERAGE(dataset_readiness[readiness_score])
At Risk Datasets = CALCULATE(DISTINCTCOUNT(dataset_trust_scores[dataset_name]), dataset_trust_scores[trust_score_band] IN {"At Risk","Blocked"})
Total Quality Checks = COUNTROWS(data_quality_results)
Failed Quality Checks = CALCULATE(COUNTROWS(data_quality_results), data_quality_results[status] = "failed")
Quality Pass Rate = DIVIDE([Total Quality Checks] - [Failed Quality Checks], [Total Quality Checks])
Schema Drift Events = CALCULATE(COUNTROWS(schema_drift_events), schema_drift_events[status] <> "unchanged")
Open Incidents = CALCULATE(COUNTROWS(incident_log), incident_log[resolution_status] = "open")
Failed Gates = CALCULATE(COUNTROWS(release_gates), release_gates[status] = "failed")
```

## Honest data notes (read before interpreting the numbers)

- **Point-in-time only.** Every CSV is a single pipeline run. There is no historical
  time series — do not add trend/“over time” visuals unless real run history is added.
- **Release gate is platform-level, not per-dataset.** `release_gates.csv` holds the 12
  whole-run gates and one overall decision. Per-dataset signals are in
  `dataset_readiness.csv` and `dataset_trust_scores.csv`.
- **Incidents are derived from the alert log.** There is no separate incident store;
  `incident_log.csv` is flattened from `alerts/alert_log.jsonl` and labeled accordingly.
- **The seed data intentionally blocks the release.** A `schema_v2` source file injects a
  quality failure, so `gold_data_quality_summary` shows **At Risk** and the overall release
  is **blocked / do_not_publish**. This is the intended teaching scenario: aggregate trust
  can look high while one critical failure still blocks BI publication.
- **Lineage edge counts differ by design.** `release_gates.csv` may show the lineage gate
  observing fewer edges than `lineage_edges.csv` lists, because the pipeline emits lineage
  in two waves (the gate reads the graph mid-run; the final graph is larger). Both are correct.

## What is intentionally NOT claimed

This dashboard does **not** represent: a live Power BI Service deployment, a connection to a
real enterprise warehouse, real production refresh, real business users, streaming/CDC, or
any cloud deployment. It is a local, reproducible reporting layer built on simulated
SaaS/ecommerce data, consistent with the rest of P5.

## Optional `.pbix` and screenshots

The `.pbix` is optional — the CSV exports + this README fully document the layer. If
you build it, save it here as `P5_Lakehouse_Data_Trust_Observability.pbix` and capture
one screenshot per page into `screenshots/` (do not add fabricated screenshots):

```text
01-executive-data-trust-overview.png
02-trusted-business-reporting.png
03-data-quality-schema-drift.png
04-release-gates-bi-readiness.png
05-incidents-lineage-metadata.png
```

## Folder contents

```text
powerbi/
├── README.md            # this file
├── sample_exports/      # reproducible flat CSVs + export_manifest.json
├── screenshots/         # 01..05 page captures (add after building .pbix)
└── P5_Lakehouse_Data_Trust_Observability.pbix   # optional, add after building
```
