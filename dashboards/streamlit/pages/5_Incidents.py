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
from components.loaders import load_alerts, load_incident_summary


setup_page("Alerts And Incidents")
render_sidebar("Alerts And Incidents")
render_header(
    "Alerts And Incidents",
    "Operational monitoring output for quality, freshness, schema, SLO, and release-gate risks.",
)

alerts = load_alerts()
incident_summary = load_incident_summary()

total_alerts = len(alerts)
open_alerts = int((alerts.get("resolution_status") == "open").sum()) if not alerts.empty and "resolution_status" in alerts else 0
resolved_alerts = int((alerts.get("resolution_status") == "resolved").sum()) if not alerts.empty and "resolution_status" in alerts else 0
high_or_critical = int((alerts.get("severity").astype(str).str.lower().isin(["high", "critical"])).sum()) if not alerts.empty and "severity" in alerts else 0
incident_count = 1 if incident_summary else 0

metric_grid(
    [
        ("Total Alerts", total_alerts, "Alert records in local alert log"),
        ("Open Alerts", open_alerts, "Alerts still open"),
        ("Resolved Alerts", resolved_alerts, "Alerts marked resolved"),
        ("High/Critical Alerts", high_or_critical, "High and critical severity alerts"),
        ("Incident Summaries", incident_count, "Generated incident markdown summaries"),
        ("MTTR", "n/a", "No resolved incident duration artifact is generated"),
    ],
    columns=6,
)

left, right = st.columns(2)
with left:
    render_count_chart(alerts, "severity", "Alert Severity Distribution")
with right:
    render_count_chart(alerts, "alert_type", "Alert Type Distribution")

section_header("Recent Alerts", "Alert records include business impact and recommended action.")
recent = alerts.sort_values("timestamp", ascending=False).head(25) if not alerts.empty and "timestamp" in alerts else alerts
render_small_table(
    recent,
    ["timestamp", "severity", "alert_type", "dataset_name", "source_system", "business_impact", "recommended_action", "resolution_status"],
    height=380,
)

section_header("Incident Summary", "Latest generated local incident summary.")
if incident_summary:
    with st.expander("Latest incident details", expanded=True):
        st.markdown(incident_summary)
else:
    st.info("Run make validate-platform to generate this artifact.")

render_footer()
