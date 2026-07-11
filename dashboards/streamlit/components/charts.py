from __future__ import annotations

import pandas as pd
import streamlit as st


def render_bar_chart(frame: pd.DataFrame, index_col: str, value_col: str, title: str) -> None:
    st.subheader(title)
    if frame.empty or index_col not in frame or value_col not in frame:
        st.info("Run make validate-platform to generate this artifact.")
        return
    chart_frame = frame[[index_col, value_col]].copy()
    chart_frame[value_col] = pd.to_numeric(chart_frame[value_col], errors="coerce").fillna(0)
    st.bar_chart(chart_frame.set_index(index_col), use_container_width=True)


def render_count_chart(frame: pd.DataFrame, column: str, title: str) -> None:
    st.subheader(title)
    if frame.empty or column not in frame:
        st.info("Run make validate-platform to generate this artifact.")
        return
    counts = frame[column].fillna("unknown").astype(str).value_counts().rename("count").to_frame()
    st.bar_chart(counts, use_container_width=True)


def render_small_table(frame: pd.DataFrame, columns: list[str] | None = None, height: int = 320) -> None:
    if frame.empty:
        st.info("Run make validate-platform to generate this artifact.")
        return
    view = frame
    if columns:
        available = [column for column in columns if column in frame.columns]
        if available:
            view = frame[available]
    st.dataframe(view, use_container_width=True, hide_index=True, height=height)
