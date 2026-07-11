from __future__ import annotations

import sys
from pathlib import Path


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.data_health_view import render_data_health
from components.layout import render_footer, render_header, render_sidebar, setup_page


setup_page("Data Health Command Center")
render_sidebar("Data Health")
render_header(
    "Data Health Command Center",
    "The main observability screenshot page for dataset readiness, source health, trust scores, release gates, and alerts.",
)
render_data_health()
render_footer()
