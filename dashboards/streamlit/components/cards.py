from __future__ import annotations

from typing import Iterable

import pandas as pd
import streamlit as st


STATUS_COLORS = {
    "ready": "#16803c",
    "trusted": "#16803c",
    "passed": "#16803c",
    "pass": "#16803c",
    "healthy": "#16803c",
    "open": "#b7791f",
    "warning": "#b7791f",
    "watch": "#b7791f",
    "at_risk": "#b7791f",
    "failed": "#b42318",
    "fail": "#b42318",
    "blocked": "#b42318",
    "critical": "#b42318",
    "quarantine": "#b42318",
    "missing": "#6b7280",
    "unknown": "#6b7280",
}


def status_color(status: object) -> str:
    key = str(status or "unknown").strip().lower().replace(" ", "_")
    return STATUS_COLORS.get(key, "#475467")


def status_badge(label: object) -> str:
    text = str(label or "unknown")
    color = status_color(text)
    return (
        f"<span style='background:{color}1a;color:{color};border:1px solid {color}55;"
        "padding:0.18rem 0.5rem;border-radius:999px;font-size:0.78rem;font-weight:700;'>"
        f"{text}</span>"
    )


def metric_grid(metrics: Iterable[tuple[str, object, str | None]], columns: int = 4) -> None:
    items = list(metrics)
    if not items:
        return
    for offset in range(0, len(items), columns):
        row = st.columns(columns)
        for column, item in zip(row, items[offset : offset + columns]):
            label, value, help_text = item
            column.metric(label, value, help=help_text)


def status_counts(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    if frame.empty or column not in frame:
        return pd.DataFrame(columns=[column, "count"])
    return frame[column].fillna("unknown").astype(str).value_counts().rename_axis(column).reset_index(name="count")


def render_status_summary(frame: pd.DataFrame, column: str, title: str) -> None:
    st.subheader(title)
    counts = status_counts(frame, column)
    if counts.empty:
        st.info("Run make validate-platform to generate this artifact.")
        return
    cols = st.columns(min(4, len(counts)))
    for idx, (_, row) in enumerate(counts.iterrows()):
        with cols[idx % len(cols)]:
            st.markdown(status_badge(row[column]), unsafe_allow_html=True)
            st.metric("Count", int(row["count"]))
