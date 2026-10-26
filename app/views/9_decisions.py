"""Portfolio what-if, hedge-selection, and optimization analysis."""

import streamlit as st

from app import state, theme
from app.charts import extras as charts
from app.components import kit
from riskkit.decisions.hedge import best_hedges
from riskkit.decisions.optimize import compare_splits, min_es_weights, min_vol_weights
from riskkit.decisions.whatif import what_if
from riskkit.portfolio.construction import simple_asset_returns

cfg = state.config()
kit.page_title(
    "Decisions",
    "Check a trade before making it, find the position that cuts risk the most, and "
    "search for the split of money with the least risk.",
)
sc = state.scenarios(cfg)
trade, hedge_tab, opt = st.tabs(["What-if trade", "Best hedge", "Optimizer"])

with trade:
    c1, c2, c3 = st.columns([1, 1, 1.4])
    stock = c1.selectbox("Stock", list(sc.weights.index))
    amount = c2.number_input("Buy (+) or sell (−), $", -sc.value, 5 * sc.value, 1_000_000.0, 250_000.0, format="%.0f")
    funding = c3.radio(
        "Paid for by",
        ["pro_rata", "cash"],
        horizontal=True,
        format_func={"pro_rata": "selling a bit of everything else", "cash": "new cash"}.get,
    )
    try:
        w = what_if(sc, stock, float(amount), funding)
        kit.kpis(
            [
                kit.Kpi(
                    "VaR before → after",
                    f"{theme.money(w['var_before'])} → {theme.money(w['var_after'])}",
                    theme.signed_money(w["var_after"] - w["var_before"]),
                    "within" if w["var_after"] <= w["var_before"] else "watch",
                ),
                kit.Kpi(
                    "ES before → after",
                    f"{theme.money(w['es_before'])} → {theme.money(w['es_after'])}",
                    theme.signed_money(w["es_after"] - w["es_before"]),
                ),
                kit.Kpi("Value after", theme.money(w["value_after"])),
            ]
        )
        kit.chart(
            charts.weights_compare(w["weights_before"], w["weights_after"], ("Now", "After the trade")),
            "The split before and after",
            key="wi",
        )
    except ValueError as exc:
        st.error(str(exc))

with hedge_tab:
    limit = st.slider("Largest hedge to consider (share of the portfolio)", 0.25, 2.0, 2.0, 0.25)
    h = best_hedges(sc, cfg.benchmark, max_size=limit)
    best = h.iloc[0]
    kit.note(
        f"Best single hedge: <b>short {theme.money(-best['amount'])} of {best['instrument']}</b>, cutting VaR from "
        f"{theme.money(best['var_before'])} to {theme.money(best['var_after'])} ({best['reduction']:.0%} less). "
        "A short position gains when that stock falls, offsetting losses elsewhere."
    )
    kit.chart(charts.hedge_chart(h), "VaR reduction from the best-sized hedge in each instrument", key="hedge")
    kit.table(
        h,
        [
            kit.Col("instrument", "Instrument"),
            kit.Col("amount", "Best position", theme.money, num=True),
            kit.Col("var_after", "VaR after", theme.money, num=True),
            kit.Col("reduction", "Reduction", theme.pct, num=True),
        ],
        download="hedges",
    )

with opt:
    c1, c2 = st.columns(2)
    goal = c1.radio(
        "Goal",
        ["es", "vol"],
        horizontal=True,
        format_func={"es": "Lowest Expected Shortfall", "vol": "Lowest volatility"}.get,
    )
    cap = c2.slider("Maximum per stock", 0.10, 1.0, 0.25, 0.05, format="%.2f")
    try:
        new = (min_es_weights if goal == "es" else min_vol_weights)(sc, cap)
        cmp = compare_splits(sc, new, simple_asset_returns(state.clean_data(cfg), cfg.cleaning.return_type))
        kit.table(
            cmp,
            [
                kit.Col("split", "Split"),
                kit.Col("VaR", "VaR", theme.money, num=True),
                kit.Col("ES", "ES", theme.money, num=True),
                kit.Col("volatility", "Volatility / yr", lambda v: theme.pct(v, 1), num=True),
                kit.Col("return", "Past return / yr", lambda v: theme.pct(v, 1), num=True),
                kit.Col("largest weight", "Largest weight", lambda v: theme.pct(v, 0), num=True),
            ],
        )
        kit.chart(
            charts.weights_compare(sc.weights, new, ("Today", "Optimized")),
            "Today's split vs the optimized one",
            "Lower risk usually means giving up some past return: the table shows both.",
            key="opt",
        )
        if st.button("Use the optimized split everywhere", type="primary"):
            state.apply_custom_weights(tuple(float(x) for x in (new / new.sum()).reindex(cfg.tickers).fillna(0)))
            st.success("Applied: every page now uses this split (Portfolio page, Custom weights).")
    except ValueError as exc:
        st.error(str(exc))
