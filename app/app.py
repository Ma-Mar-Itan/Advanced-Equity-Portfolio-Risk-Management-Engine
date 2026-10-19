"""Streamlit entry point. Run from the V2 folder:  streamlit run app/app.py

Thin on purpose: page setup, theme, navigation, header. One page per module.
"""

import os
import sys
from pathlib import Path

# Streamlit puts this script's folder (app/) first on sys.path, so a bare
# `import app` would find this file (app.py) instead of the app/ package and
# import itself. Drop app/ from the path and always put the V2 root first.
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent


def _norm(p):
    return os.path.normcase(str(Path(p or ".").resolve()))


sys.path[:] = [p for p in sys.path if _norm(p) not in (_norm(APP_DIR), _norm(ROOT))]
sys.path.insert(0, str(ROOT))
_cached = sys.modules.get("app")
if _cached is not None and not hasattr(_cached, "__path__"):  # stale app.py module, not the package
    del sys.modules["app"]

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Equity Risk", page_icon=":material/monitoring:", layout="wide",
                   initial_sidebar_state="collapsed")

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
