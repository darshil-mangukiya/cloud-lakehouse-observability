from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_ROOT = PROJECT_ROOT / "dashboards/streamlit"
if str(STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(STREAMLIT_ROOT))

from app import main


if __name__ == "__main__":
    main()
