"""Market-data selection, provenance, and coverage page."""

import pandas as pd
import streamlit as st

from app import controls, state
from app.charts.data import growth_chart, growth_of_one_dollar
from app.components import kit
from riskkit.data.collect import summary_table

cfg = state.config()
kit.page_title(
    "Data",
    "Daily prices for every stock, adjusted for splits and dividends and converted to "
    "US dollars. Add any stock in the world by name.",
)

with kit.panel("data_settings"):
    changes = controls.data_settings(cfg)
    added = controls.stock_search()
if changes:
    state.update_config(**changes)
    st.rerun()
if added and added not in cfg.tickers:
    state.update_config(tickers=(*cfg.tickers, added))
    st.rerun()

md = state.market_data(cfg)
prices = md.prices.loc[pd.Timestamp(cfg.start) :].dropna(how="all")
kit.kpis(
    [
        kit.Kpi(
            "Stocks",
            str(len(prices.columns)),
            f"{len(md.failed)} not found" if md.failed else "all found",
            "breach" if md.failed else None,
        ),
        kit.Kpi("Trading days", f"{len(prices):,}", f"{prices.index[0]:%b %Y} to {md.as_of:%d %b %Y}"),
        kit.Kpi("Benchmark", cfg.benchmark, md.origin.get(cfg.benchmark, "")),
        kit.Kpi("Risk-free rate", f"{md.risk_free.iloc[-1] * 252:.2%}", md.origin["risk-free"]),
    ]
)

growth = growth_of_one_dollar(prices.dropna())
best, worst = growth.iloc[-1].idxmax(), growth.iloc[-1].idxmin()
kit.chart(
    growth_chart(growth),
    "Same years, very different journeys",
    f"$1 in {best} grew to <b>${growth[best].iloc[-1]:,.0f}</b>; $1 in {worst} to "
    f"<b>${growth[worst].iloc[-1]:,.0f}</b>.",
    "Log scale: each gridline step is ten times more money.",
    key="growth",
)

with kit.panel("summary"):
    kit.section("What was collected", aside="one row per stock")
    table = summary_table(md, cfg).reset_index()
    kit.table(
        table,
        [
            kit.Col("ticker", "Stock"),
            kit.Col("name", "Name"),
            kit.Col("sector", "Sector"),
            kit.Col("currency", "Currency"),
            kit.Col("first price", "First price", kit.day),
            kit.Col("days since start", "Days", "{:,}", num=True),
            kit.Col("source", "Source", dim=True),
        ],
        download="data_summary",
    )
if st.button("Re-download latest prices", help="Ignore saved files and fetch again"):
    state.refresh_market_data(cfg)
    st.rerun()
