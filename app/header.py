"""The thin identity line under the navigation: what portfolio, as of when, from where."""

from __future__ import annotations

import streamlit as st

from app import state, theme
from app.components import kit


def render() -> None:
    """Draw the identity block for the current settings (or an error if data cannot load)."""
    cfg = state.config()
    try:
        md = state.market_data(cfg)
    except Exception as exc:  # no data at all: say so plainly and stop the page
        st.error(f"Could not load prices: {exc}")
        st.stop()
    sources = sorted({v.split(" ")[0] for k, v in md.origin.items() if k in md.prices.columns})
    failed = f'<span class="rk-flag">Not found: {kit.esc(", ".join(md.failed))}</span>' if md.failed else ""
    kit.render(f"""
<div class="rk-ident">
  <div class="rk-ident-name">{len(md.prices.columns)}-stock portfolio</div>
  <div class="rk-ident-meta">
    <span>As of <b>{md.as_of:%d %b %Y}</b></span>
    <span>Value <b>{kit.esc(theme.money(cfg.portfolio_value))}</b></span>
    <span>From <b>{cfg.start:%d %b %Y}</b></span>
    <span>Prices <b>{kit.esc(", ".join(sources))}</b>{" (offline)" if cfg.offline else ""}</span>
    {failed}
  </div>
</div>""")
    st.html('<div style="border-bottom:1px solid var(--rule);margin:2px 0 0 0"></div>')
