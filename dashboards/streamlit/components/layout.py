from __future__ import annotations

import streamlit as st

from components.loaders import MISSING_ARTIFACT_MESSAGE, PROJECT_ROOT, latest_artifact_timestamp


def setup_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="▣", layout="wide")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e4e7ec;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        label[data-testid="stMetricLabel"],
        label[data-testid="stMetricLabel"] p {
            font-size: 0.82rem;
            color: #475467 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #101828 !important;
        }
        .local-banner {
            border: 1px solid #d0d5dd;
            border-left: 4px solid #0f766e;
            background: #f8fafc;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            color: #344054;
            margin: 0.75rem 0 1rem 0;
        }
        .section-note {
            color: #667085;
            font-size: 0.94rem;
            margin-top: -0.35rem;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(page_title: str, subtitle: str | None = None) -> None:
    st.title(page_title)
    if subtitle:
        st.caption(subtitle)
    st.markdown(
        """
        <div class="local-banner">
        Local GitHub-ready dashboard. It reads generated artifacts from this repository and does not claim live production or cloud deployment.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(active_page: str) -> None:
    st.sidebar.title("Lakehouse Observability")
    st.sidebar.caption("Local command center")
    st.sidebar.markdown(f"**Active page:** {active_page}")
    st.sidebar.markdown(f"**Last updated:** {latest_artifact_timestamp()}")
    if st.sidebar.button("Refresh artifacts", use_container_width=True):
        st.rerun()
    st.sidebar.divider()
    st.sidebar.markdown("Generate artifacts:")
    st.sidebar.code("make validate-platform", language="bash")
    st.sidebar.markdown("Run dashboard:")
    st.sidebar.code("streamlit run dashboards/streamlit/app.py", language="bash")
    st.sidebar.caption(f"Project root: `{PROJECT_ROOT.name}`")


def section_header(title: str, note: str | None = None) -> None:
    st.subheader(title)
    if note:
        st.markdown(f"<div class='section-note'>{note}</div>", unsafe_allow_html=True)


def missing_artifact() -> None:
    st.info(MISSING_ARTIFACT_MESSAGE)


def render_footer() -> None:
    st.divider()
    st.caption("This platform makes lakehouse data reliable, observable, governed, and safe for BI consumption.")
