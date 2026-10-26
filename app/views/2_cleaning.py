"""Data-cleaning controls, diagnostics, validation, and downloads."""

from dataclasses import replace

import streamlit as st

from app import controls, state
from app.charts.cleaning import distribution_before_after, returns_timeline, rolling_vol_chart
from app.components import kit
from app.components.data_outputs import render_data_outputs
from riskkit.volatility.rolling import rolling_volatility

cfg = state.config()
kit.page_title(
    "Cleaning",
    "Line up the dates, fill gaps, catch stale prices, turn prices into returns, "
    "and optionally clip extremes. Every change is logged.",
)

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("clean_controls"):
    choice = controls.cleaning_controls(cfg.cleaning)
if isinstance(choice, str):
    left.error(choice)
elif choice != cfg.cleaning:
    state.update_config(cleaning=choice)
    st.rerun()

try:
    cd = state.clean_data(cfg)
except ValueError as exc:  # usually a bad custom formula: show it and fall back to no formula
    right.error(str(exc))
    cd = state.clean_data(cfg.updated(cleaning=replace(cfg.cleaning, custom_expression="")))

with right:
    passed = sum(c.passed for c in cd.checks)
    kit.kpis(
        [
            kit.Kpi(
                "Days kept",
                f"{len(cd.returns):,}",
                f"{cd.returns.index[0]:%d %b %Y} to {cd.returns.index[-1]:%d %b %Y}",
            ),
            kit.Kpi("Prices filled", f"{cd.count('fill'):,}"),
            kit.Kpi("Stale prices", f"{cd.count('stale'):,}", cfg.cleaning.stale_action),
            kit.Kpi("Returns changed", f"{cd.changed_returns():,}", "winsorize + formula"),
            kit.Kpi(
                "Checks passed", f"{passed}/{len(cd.checks)}", None, "within" if passed == len(cd.checks) else "breach"
            ),
        ]
    )
    kit.checks({f"{c.name}: {c.detail}": c.passed for c in cd.checks})
    stock = st.selectbox("Stock to inspect", list(cd.returns.columns))
    raw, final = cd.raw_returns[stock], cd.returns[stock]
    kit.chart(
        distribution_before_after(raw, final),
        f"{stock}: daily returns, before and after",
        "Most days are small moves; the long tails are the rare big days risk is about.",
        key="dist",
    )
    kit.chart(
        returns_timeline(raw, final),
        f"{stock}: every daily return",
        "Red dots are days changed by winsorizing or the custom formula.",
        key="timeline",
    )
    window = st.select_slider("Rolling window (trading days)", [10, 21, 63, 126, 252], 21)
    rolling_vol = rolling_volatility(cd.returns, window)
    kit.chart(
        rolling_vol_chart(rolling_vol, stock),
        "Rolling volatility",
        f"How jumpy each stock was over the last {window} days, as a yearly figure. {stock} highlighted.",
        key="rollvol",
    )
    try:
        portfolio_returns, portfolio_error = state.portfolio(cfg).returns, None
    except ValueError as exc:
        portfolio_returns, portfolio_error = None, str(exc)
    render_data_outputs(
        cd,
        portfolio_returns,
        rolling_vol,
        return_type=cfg.cleaning.return_type,
        rolling_window=window,
        portfolio_error=portfolio_error,
    )
    with kit.panel("clean_log"):
        kit.section("Cleaning log", aside=f"{len(cd.log):,} entries")
        if cd.log.empty:
            kit.note("Nothing needed changing with these settings.")
        else:
            kit.table(
                cd.log.head(500),
                [
                    kit.Col("step", "Step"),
                    kit.Col("date", "Date", kit.day),
                    kit.Col("ticker", "Stock"),
                    kit.Col("detail", "What was done"),
                ],
                download="cleaning_log",
                height=320,
            )
