from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.cards import metric_grid, status_badge
from components.charts import render_bar_chart, render_count_chart, render_small_table
from components.layout import render_footer, render_header, render_sidebar, section_header, setup_page
from components.loaders import load_readiness, load_release_gates, load_trust_scores


setup_page("Release Gates")
render_sidebar("Release Gates")
render_header(
    "Release Gates",
    "BI publication safety checks that intentionally block unsafe gold data from downstream consumption.",
)

release, gates = load_release_gates()
readiness = load_readiness()
trust = load_trust_scores()

approved = int((readiness.get("readiness_status") == "ready").sum()) if not readiness.empty else 0
blocked = len(readiness) - approved if not readiness.empty else 0
failed_gates = release.get("failed_gate_count", int((gates.get("status") == "failed").sum()) if not gates.empty else 0)
warning_gates = release.get("warning_gate_count", int((gates.get("status") == "warning").sum()) if not gates.empty else 0)
release_status = release.get("release_status", "unknown")

metric_grid(
    [
        ("Release Status", release_status, "Latest local release gate status"),
        ("Publish Decision", release.get("publish_decision", "unknown"), "Whether gold data is safe to publish"),
        ("Gold Approved", approved, "Gold datasets with ready status"),
        ("Gold Blocked/At Risk", blocked, "Gold datasets not ready"),
        ("Failed Gates", failed_gates, "Critical gates with failed status"),
        ("Warning Gates", warning_gates, "Gates with warning status"),
    ],
    columns=3,
)

st.markdown(
    f"**Current publish control:** {status_badge(release_status)} "
    "Blocked local releases are intentional when quality, trust, SLO, or alert checks indicate BI risk.",
    unsafe_allow_html=True,
)

left, right = st.columns(2)
with left:
    render_count_chart(gates, "status", "Gate Status")
with right:
    render_bar_chart(trust, "dataset_name", "trust_score_overall", "Trust Score By Gold Dataset")

section_header("Release Gate Detail", "Each gate includes observed value, expected value, severity, and recommended action.")
render_small_table(gates, ["gate_name", "status", "severity", "observed", "expected", "recommended_action"], height=380)

readiness_trust = readiness.copy()
if not readiness_trust.empty and not trust.empty:
    readiness_trust = readiness_trust.merge(
        trust[["dataset_name", "trust_score_overall", "trust_score_band", "recommended_action"]],
        on="dataset_name",
        how="left",
    )

section_header("Gold Dataset Readiness", "Dataset-level safety signals used before local BI publication.")
render_small_table(
    readiness_trust,
    [
        "dataset_name",
        "row_count",
        "readiness_score",
        "readiness_status",
        "trust_score_overall",
        "trust_score_band",
        "quality_status",
        "freshness_status",
        "schema_status",
        "recommended_action",
    ],
    height=380,
)

blocked_detail = readiness_trust[readiness_trust["readiness_status"] != "ready"] if not readiness_trust.empty and "readiness_status" in readiness_trust else pd.DataFrame()
with st.expander("Blocked or at-risk dataset detail", expanded=not blocked_detail.empty):
    render_small_table(blocked_detail, height=260)

render_footer()
