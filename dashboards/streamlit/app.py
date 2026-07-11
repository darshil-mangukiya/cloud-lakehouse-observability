from __future__ import annotations

import sys
from pathlib import Path


DASHBOARD_ROOT = Path(__file__).resolve().parent
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from components.data_health_view import render_data_health
from components.layout import render_footer, render_header, render_sidebar, setup_page


def main() -> None:
    setup_page("Lakehouse Data Trust Command Center")
    render_sidebar("Data Health")
    render_header(
        "Lakehouse Data Trust Command Center",
        "Platform-level health, freshness, trust, release safety, and alerts for the local lakehouse.",
    )
    render_data_health()
    render_footer()


if __name__ == "__main__":
    main()
