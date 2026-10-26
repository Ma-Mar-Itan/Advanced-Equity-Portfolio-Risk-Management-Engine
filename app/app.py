"""Streamlit entry point for the QFI Risk Platform dashboard."""

import os
import sys
from pathlib import Path

# Streamlit places the script directory before the project root. Normalize the
# import path so ``app`` resolves to the package instead of this entry-point file.
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent


def _norm(p):
    return os.path.normcase(str(Path(p or ".").resolve()))


sys.path[:] = [p for p in sys.path if _norm(p) not in (_norm(APP_DIR), _norm(ROOT))]
sys.path.insert(0, str(ROOT))
_cached = sys.modules.get("app")
if _cached is not None and not hasattr(_cached, "__path__"):  # Remove an entry-point module cached as ``app``.
    del sys.modules["app"]

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="Equity Risk", page_icon=":material/monitoring:", layout="wide", initial_sidebar_state="collapsed"
)

from app import header  # noqa: E402
from app.components import kit  # noqa: E402

kit.inject_css()
VIEWS = Path(__file__).parent / "views"
nav = st.navigation(
    [
        st.Page(VIEWS / "1_data.py", title="1 Data", default=True),
        st.Page(VIEWS / "2_cleaning.py", title="2 Cleaning"),
        st.Page(VIEWS / "3_portfolio.py", title="3 Portfolio"),
        st.Page(VIEWS / "4_volatility.py", title="4 Volatility"),
        st.Page(VIEWS / "5_var.py", title="5 VaR & ES"),
        st.Page(VIEWS / "6_backtesting.py", title="6 Backtesting"),
        st.Page(VIEWS / "7_stress.py", title="7 Stress"),
        st.Page(VIEWS / "8_risk_sources.py", title="8 Risk sources"),
        st.Page(VIEWS / "9_decisions.py", title="9 Decisions"),
    ],
    position="top",
)
header.render()
nav.run()
