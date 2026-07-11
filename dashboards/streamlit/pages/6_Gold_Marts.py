from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.cards import metric_grid
from components.charts import render_count_chart, render_small_table
from components.layout import render_footer, render_header, render_sidebar, section_header, setup_page
from components.loaders import GOLD_MARTS, load_gold_dataset, load_gold_inventory, load_parquet_manifest


setup_page("Gold Marts And BI Outputs")
render_sidebar("Gold Marts")
render_header(
    "Gold Marts And BI Outputs",
    "Analytics-ready local gold outputs, mart definitions, row counts, and preview tables for reporting review.",
)

inventory = load_gold_inventory()
parquet_manifest = load_parquet_manifest()

csv_available = int((inventory.get("artifact_status") == "csv_available").sum()) if not inventory.empty else 0
model_available = int((inventory.get("artifact_status") == "dbt_model_available").sum()) if not inventory.empty else 0
ready = int((inventory.get("bi_readiness_status") == "ready").sum()) if not inventory.empty else 0

metric_grid(
    [
        ("Gold/Mart Assets", len(inventory), "Gold datasets plus lightweight fact/dimension views"),
        ("CSV Exports", csv_available, "Gold datasets available as local CSV output"),
        ("dbt-only Views", model_available, "Fact/dim models defined without generated CSV preview"),
        ("Ready For BI", ready, "Readiness status is ready"),
        ("Parquet Written", parquet_manifest.get("written_count", 0), "Partitioned Parquet outputs written locally"),
        ("Parquet Skipped", parquet_manifest.get("skipped_count", 0), "Parquet writes skipped if engine unavailable"),
    ],
    columns=6,
)

left, right = st.columns(2)
with left:
    render_count_chart(inventory, "artifact_status", "Gold Artifact Status")
with right:
    render_count_chart(inventory, "bi_readiness_status", "BI Readiness Status")

section_header("Gold Mart Inventory", "Business purpose, grain, owner, key metrics, row counts, and readiness.")
render_small_table(
    inventory,
    [
        "dataset_name",
        "row_count",
        "owner",
        "criticality",
        "business_purpose",
        "grain",
        "key_metrics",
        "bi_readiness_status",
        "trust_score",
        "artifact_status",
    ],
    height=420,
)

selected = st.selectbox("Preview gold mart or dbt mart asset", list(GOLD_MARTS))
preview = load_gold_dataset(selected)
section_header(f"Preview: {selected}", "CSV preview is shown when a generated gold export exists.")
if preview.empty:
    st.info("No generated CSV preview exists for this asset. If it is a dbt-only fact/dimension view, run dbt against PostgreSQL to inspect the model.")
else:
    render_small_table(preview, height=380)

with st.expander("Selected mart definition", expanded=False):
    st.json(GOLD_MARTS[selected])

render_footer()
