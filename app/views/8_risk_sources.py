"""Asset, sector, and benchmark-relative risk attribution."""

from dataclasses import replace

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import extras as charts
from app.components import kit
from riskkit.attribution.euler import active_risk, attribution_table, diversification

cfg = state.config()
kit.page_title(
    "Where the risk comes from",
    "The portfolio's VaR and ES split into each stock's share, like "
    "splitting a bill by what each person ate. The shares add up to the total.",
)
md = state.market_data(cfg)
sectors = pd.Series({t: md.profiles[t].sector for t in md.prices.columns})

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("rs_controls"):
    model = st.radio(
        "VaR model",
        list(controls.VAR_LABELS),
        list(controls.VAR_LABELS).index(cfg.var.model),
        format_func=controls.VAR_LABELS.get,
    )
    measure = st.radio(
        "Split",
        ["ES", "VaR"],
        horizontal=True,
        format_func={"ES": "Expected Shortfall (exact)", "VaR": "VaR (smoothed)"}.get,
    )
    kit.note(
        "Scenarios: the last window of days, rebuilt from today's exact holdings, so totals can differ slightly "
        "from the VaR page."
    )
if model != cfg.var.model:
    state.update_config(var=replace(cfg.var, model=model))
    st.rerun()

sc = state.scenarios(cfg)
table, div = attribution_table(sc, sectors), diversification(sc)
act = active_risk(sc, state.portfolio(cfg).returns, md.benchmark)
col = "es_usd" if measure == "ES" else "var_usd"
top = table.sort_values(col, ascending=False).iloc[0]

with right:
    kit.kpis(
        [
            kit.Kpi(
                f"Portfolio {measure}",
                theme.money(div["es" if measure == "ES" else "var"]),
                f"{cfg.confidence:.0%}, 1 day",
            ),
            kit.Kpi(
                "Biggest source",
                str(top["stock"]),
                f"{top['es_share' if measure == 'ES' else 'var_share']:.0%} of risk, {top['weight']:.0%} of money",
            ),
            kit.Kpi("Stocks alone would add to", theme.money(div["sum_standalone"]), "sum of stand-alone VaRs"),
            kit.Kpi(
                "Saved by mixing",
                theme.money(div["benefit"]),
                f"{div['benefit_share']:.0%} of the stand-alone total",
                "within",
            ),
            kit.Kpi("Tracking error", theme.pct(act["tracking error"], 1), f"vs {cfg.benchmark}, per year"),
        ]
    )
    kit.chart(
        charts.share_chart(table, measure),
        f"Share of the money vs share of the {measure}",
        "Bars taller in teal than grey: that stock carries more risk than its money share.",
        key="share",
    )
    by_sector = table.groupby("sector")[col].sum()
    kit.chart(charts.sector_chart(by_sector, measure), f"{measure} by sector", key="sector")
    with kit.panel("rs_table"):
        kit.section("Every stock", aside=f"{measure} split, $")
        kit.table(
            table,
            [
                kit.Col("stock", "Stock"),
                kit.Col("sector", "Sector", dim=True),
                kit.Col("weight", "Money", theme.pct, num=True),
                kit.Col("var_usd", "VaR share", theme.money, num=True),
                kit.Col("var_share", "% of VaR", theme.pct, num=True),
                kit.Col("es_usd", "ES share", theme.money, num=True),
                kit.Col("es_share", "% of ES", theme.pct, num=True),
                kit.Col("standalone_usd", "VaR if alone", theme.money, num=True),
            ],
            download="risk_by_stock",
        )
    with kit.panel("rs_active"):
        kit.section(
            f"Risk against the market ({cfg.benchmark})", "How far our basket strays from simply holding the market."
        )
        kit.kpis(
            [
                kit.Kpi("Beta", f"{act['beta']:.2f}", "moves per 1% market move"),
                kit.Kpi("Tracking error", theme.pct(act["tracking error"], 1), "spread of the yearly gap"),
                kit.Kpi("VaR of the gap", theme.money(act["active VaR"]), "1 day, vs the market"),
                kit.Kpi("Information ratio", f"{act['information ratio']:.2f}", "extra return per unit of gap"),
            ]
        )
