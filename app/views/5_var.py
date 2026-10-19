"""Page 5, VaR & ES (Module 5): on a bad day, how much could we lose?"""

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import var as charts
from app.components import kit
from riskkit.var.checks import var_checks

cfg = state.config()
kit.page_title("VaR & Expected Shortfall", "<b>VaR</b>: the loss we expect to beat on most days. "
               "<b>Expected Shortfall</b>: the average loss on the days we don't.")

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("var_controls"):
    choice = controls.var_controls(cfg)
if isinstance(choice, str):
    left.error(choice)
elif any(getattr(cfg, k) != v for k, v in choice.items()):
    state.update_config(**choice)
    st.rerun()

results = state.var_today(cfg)
res = next(r for r in results if r.model == cfg.var.model)
rolling = state.var_rolling(cfg)
c, h, days_in = cfg.confidence, cfg.var.horizon, round(1 / (1 - cfg.confidence))

with right:
    kit.kpis([
        kit.Kpi(f"1-day VaR {c:.1%}", theme.money(res.var_1d_usd), f"{theme.pct(res.var_1d)} of {theme.money(res.value)}"),
        kit.Kpi("1-day Expected Shortfall", theme.money(res.es_1d_usd), theme.pct(res.es_1d)),
        kit.Kpi(f"{h}-day VaR", theme.money(res.var_h_usd), theme.pct(res.var_h)),
        kit.Kpi(f"{h}-day Expected Shortfall", theme.money(res.es_h_usd), theme.pct(res.es_h)),
        kit.Kpi("Scenarios", f"{len(res.scenarios):,}", f"{cfg.window} past days, {res.model}"),
    ])
    kit.note(f"In plain words: on {days_in - 1} trading days out of {days_in} we expect to lose less than "
             f"<b>{theme.money(res.var_1d_usd)}</b> tomorrow; on the worst 1 in {days_in}, we lose "
             f"<b>{theme.money(res.es_1d_usd)}</b> on average.")
    kit.checks({f"{k.name}: {k.detail}": k.passed for k in var_checks(state.portfolio(cfg).log_returns, cfg,
                                                                       results, rolling[cfg.var.model])})
    kit.chart(charts.scenario_histogram(res), f"{len(res.scenarios)} possible tomorrows",
              "Each bar counts past days replayed on today's portfolio" +
              (", rescaled to today's volatility." if res.model != "HS" else "."), key="hist")
    kit.chart(charts.tail_chart(res), "The worst scenarios up close",
              "Red bars are the tail: VaR is the edge, ES is their average.", key="tail")
    kit.chart(charts.models_chart(results), "Four models, today", key="models",
              finding="Scaled models follow today's volatility; plain history remembers every crash in the window.")
    with kit.panel("var_grid"):
        kit.section("Confidence × window", aside=f"1-day VaR, {res.model}, % of value")
        grid = state.var_grid(cfg).reset_index().rename(columns={"index": "confidence"})
        kit.table(grid, [kit.Col("confidence", "Confidence")] +
                  [kit.Col(col, col, theme.pct, num=True) for col in grid.columns[1:]])
    kit.chart(charts.rolling_chart(rolling, cfg.var.model, cfg.portfolio_value), "Rolling VaR against what happened",
              "Each day's VaR was computed using only earlier days. Red dots: losses beyond the "
              f"{cfg.var.model} VaR. Click the legend to add models.", key="roll")
    kit.chart(charts.var_vs_es_chart(rolling[cfg.var.model], cfg.portfolio_value), "VaR and Expected Shortfall over time",
              key="vares")
