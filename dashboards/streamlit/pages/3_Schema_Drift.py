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
from components.loaders import load_contract_reports, load_schema_history


setup_page("Schema Drift")
render_sidebar("Schema Drift")
render_header(
    "Schema Drift And Source Contracts",
    "Schema evolution, safe renames, contract outcomes, and quarantine evidence for local source extracts.",
)

schema_history = load_schema_history()
contracts = load_contract_reports()

drift_events = len(schema_history)
breaking = int((schema_history.get("breaking") == True).sum()) if not schema_history.empty and "breaking" in schema_history else 0
compatible = int((schema_history.get("status") == "compatible_evolution").sum()) if not schema_history.empty and "status" in schema_history else 0
contract_failures = int((contracts.get("status").astype(str).str.upper().isin(["FAIL", "QUARANTINE"])).sum()) if not contracts.empty and "status" in contracts else 0

metric_grid(
    [
        ("Schema Events", drift_events, "Schema registry history records"),
        ("Compatible Evolutions", compatible, "Safe additive changes or approved renames"),
        ("Breaking Events", breaking, "Removed columns or type changes"),
        ("Contract Reports", len(contracts), "Generated source contract validation reports"),
        ("Contract Failures", contract_failures, "FAIL or QUARANTINE outcomes"),
    ],
    columns=5,
)

left, right = st.columns(2)
with left:
    render_count_chart(schema_history, "source_system", "Drift Events By Source")
with right:
    render_count_chart(contracts, "status", "Contract Outcomes")

section_header("Schema Drift Detail", "Schema versions, added/removed columns, type changes, safe renames, and breaking flags.")
render_small_table(
    schema_history,
    [
        "detected_at",
        "source_system",
        "previous_version",
        "current_version",
        "status",
        "added_columns",
        "removed_columns",
        "type_changes",
        "safe_renames",
        "breaking",
    ],
    height=360,
)

section_header("Source Contract Validation", "Contract outcomes include row counts, violation counts, source ownership, and downstream dependencies.")
render_small_table(
    contracts,
    [
        "validated_at",
        "source_system",
        "dataset_name",
        "status",
        "violation_count",
        "row_count",
        "owner",
        "criticality_tier",
        "downstream_dependencies",
    ],
    height=360,
)

with st.expander("Sample schema change record", expanded=False):
    if schema_history.empty:
        st.info("Run make validate-platform to generate this artifact.")
    else:
        st.json(schema_history.iloc[-1].to_dict())

render_footer()
