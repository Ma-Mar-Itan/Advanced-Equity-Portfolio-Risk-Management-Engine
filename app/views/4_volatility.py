"""Page 4, Volatility (Module 4): how jumpy the market is now, four ways, and why it matters."""

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import volatility as charts
from app.components import kit
from riskkit.volatility.analysis import leverage_effect, regime_table, scale_to_today, volatility_regimes
from riskkit.volatility.base import annualize

cfg = state.config()
kit.page_title("Volatility", "Volatility is the typical size of a day's move. It changes over time and storms "
               "cluster, so what matters is how jumpy things are <i>now</i>.")

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("vol_controls"):
    spec, view = controls.volatility_controls(cfg, ["Portfolio", *state.clean_data(cfg).returns.columns])
if isinstance(spec, str):
    left.error(spec)
elif spec != cfg.volatility:
    state.update_config(volatility=spec)
    st.rerun()

returns, fits, yearly = state.series_for(cfg, view["series"]), state.vol_fits(cfg, view["series"]), view["yearly"]
gjr = fits["GJR-GARCH"]
unit = "a year" if yearly else "a day"


def fmt(v: float) -> str:
    """A daily volatility shown as a % (yearly or daily, as chosen)."""
    return f"{(annualize(v) if yearly else v):.1%}"


with right:
    kit.kpis([kit.Kpi(f"{n} today", fmt(f.next_day), f"in {cfg.volatility.horizon}d: {fmt(f.forecast[-1])}")
              for n, f in fits.items()] + [kit.Kpi("Long-run (GJR)", f"{gjr.params.get('long-run vol (yearly)', 0):.1%}",
                                                 "where storms fade to")])
    kit.chart(charts.comparison_chart(fits, yearly), f"{view['series']}: four estimates of the same volatility",
              "Rolling reacts late and drops crashes all at once; EWMA and GARCH react the next day.", key="cmp")
    pick = st.selectbox("Model for the clustering, residual, regime and rescaling charts", list(fits)[::-1],
                        help="GJR-GARCH by default; switch to EWMA or GARCH to see the brief's charts for those models.")
    m = fits[pick]
    kit.chart(charts.clustering_chart(returns, m), "Bad days cluster together",
              f"The line is daily returns; the band is ±2 {pick} volatilities. Red days broke the band.", key="cluster")
    c1, c2 = st.columns(2)
    with c1:
        kit.chart(charts.leverage_chart(leverage_effect(returns)), "After a big fall, the next days are wilder",
                  "Measured straight from the data, no model.", key="lev")
    with c2:
        kit.chart(charts.news_impact_chart(fits, yearly), "Leverage effect in the models",
                  f"GJR's γ = {gjr.params['gamma']:.3f}: down days raise volatility more.", key="nic")
    kit.chart(charts.forecast_chart(fits, yearly), f"Forecast for the next {cfg.volatility.horizon} days",
              "GARCH models drift back towards the long-run level; EWMA and rolling stay flat.", key="fc")
    with kit.panel("vol_params"):
        kit.section("Fitted parameters", aside="ω tiny by design: it sets the long-run level")
        names = sorted({k for f in fits.values() for k in f.params}, key=lambda k: list(gjr.params).index(k)
                       if k in gjr.params else 99)
        table = pd.DataFrame([{"parameter": k, **{n: f.params.get(k) for n, f in fits.items()}} for k in names])
        kit.table(table, [kit.Col("parameter", "Parameter")] +
                  [kit.Col(n, n, lambda v: f"{v:,.4g}", num=True) for n in fits])
    z = m.std_residuals(returns)
    kit.chart(charts.residuals_chart(returns, z), f"Standardized residuals: does {pick} explain the wild days?",
              f"Extreme-day score (kurtosis; normal = 3): raw returns <b>{returns.kurt() + 3:.1f}</b>, after dividing "
              f"by {pick} volatility <b>{z.kurt() + 3:.1f}</b>.", key="resid")
    regimes = regime_table(returns, volatility_regimes(m.sigma))
    kit.chart(charts.regime_chart(regimes), "Volatility regimes compared",
              f"Days split into thirds by {pick} volatility: big losses live almost entirely in the stormy third.",
              key="regchart")
    with kit.panel("regimes"):
        kit.section("Calm, normal and stormy periods", aside=f"days split in thirds by {pick} volatility")
        kit.table(regimes,
                  [kit.Col("regime", "Regime"), kit.Col("share of days", "Days", theme.pct, num=True),
                   kit.Col("typical move", "Typical daily move", theme.pct, num=True),
                   kit.Col("worst day", "Worst day", theme.pct, num=True),
                   kit.Col("days below -3%", "Days below −3%", "{:,}", num=True)])
    kit.chart(charts.scaled_chart(returns, scale_to_today(returns, m)), f"Raw vs {pick}-scaled returns",
              f"Past returns replayed at today's {pick} volatility ({fmt(m.next_day)} {unit}). Module 5 uses these "
              "rescaled days to estimate "
              "tomorrow's risk.", key="scaled")
