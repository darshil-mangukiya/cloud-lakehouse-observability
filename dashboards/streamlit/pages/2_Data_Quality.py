from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.cards import metric_grid
from components.charts import render_count_chart, render_small_table
from components.layout import render_footer, render_header, render_sidebar, section_header, setup_page
from components.loaders import load_quality_reports, load_quality_summary, load_rejected_records, load_row_count_anomalies


setup_page("Data Quality")
render_sidebar("Data Quality")
render_header(
    "Data Quality",
    "Great Expectations-style validation results, failed checks, rejected records, and row-count anomaly evidence.",
)

quality_summary = load_quality_summary()
quality_reports, quality_checks = load_quality_reports()
rejected = load_rejected_records()
anomalies = load_row_count_anomalies()

check_count = int(pd.to_numeric(quality_summary.get("check_count"), errors="coerce").fillna(0).sum()) if not quality_summary.empty else 0
failed_count = int(pd.to_numeric(quality_summary.get("failed_check_count"), errors="coerce").fillna(0).sum()) if not quality_summary.empty else 0
passed_count = max(check_count - failed_count, 0)
warning_count = int((quality_checks.get("status") == "warning").sum()) if not quality_checks.empty and "status" in quality_checks else 0
failed_datasets = int((quality_summary.get("quality_status", quality_summary.get("status")) == "failed").sum()) if not quality_summary.empty else 0
null_breaches = len(quality_checks[(quality_checks.get("check_name", "").astype(str).str.contains("null", case=False, na=False)) & (quality_checks.get("status") == "failed")]) if not quality_checks.empty else 0
duplicate_issues = len(quality_checks[(quality_checks.get("check_name", "").astype(str).str.contains("unique|duplicate", case=False, na=False)) & (quality_checks.get("status") == "failed")]) if not quality_checks.empty else 0
row_anomaly_failures = int((anomalies.get("status") == "failed").sum()) if not anomalies.empty and "status" in anomalies else 0

metric_grid(
    [
        ("Total Checks", check_count, "Validation checks from local quality reports"),
        ("Passed Checks", passed_count, "Checks without failure"),
        ("Failed Checks", failed_count, "Checks with failed status"),
        ("Warning Checks", warning_count, "Checks with warning status when present"),
        ("Failed Datasets", failed_datasets, "Silver datasets with failed quality status"),
        ("Rejected Records", len(rejected), "Records exported to failed-record files"),
        ("Null Breaches", null_breaches, "Failed null-threshold checks"),
        ("Duplicate Issues", duplicate_issues, "Failed uniqueness/duplicate checks"),
        ("Row Count Anomalies", row_anomaly_failures, "Failed row-count anomaly checks"),
        ("Referential Issues", "n/a", "No explicit referential-integrity report is generated"),
    ],
    columns=5,
)

left, right = st.columns(2)
with left:
    render_count_chart(quality_summary, "quality_status" if "quality_status" in quality_summary else "status", "Quality Pass/Fail Summary")
with right:
    failed_checks = quality_checks[quality_checks["status"] == "failed"] if not quality_checks.empty and "status" in quality_checks else quality_checks
    render_count_chart(failed_checks, "dataset_name", "Failed Checks By Dataset")

section_header("Quality Report Details", "Per-dataset validation summaries from the local quality framework.")
render_small_table(quality_summary, height=280)

with st.expander("Check-level validation results", expanded=False):
    render_small_table(
        quality_checks,
        ["dataset_name", "check_name", "status", "severity", "observed_value", "threshold", "failed_records"],
        height=360,
    )

section_header("Rejected Records", "Records rejected during standardization or validation are kept for remediation review.")
render_small_table(rejected.head(100) if not rejected.empty else rejected, height=280)

section_header("Row Count Anomalies", "Local anomaly checks compare observed row counts with baseline row counts.")
render_small_table(anomalies, height=260)

render_footer()
