"""Page 6, Backtesting (Module 6): did the VaR forecasts hold up, and which model is best?"""

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import backtest as charts
from app.charts.var import rolling_chart
from app.components import kit
from riskkit.backtest.checks import backtest_checks
from riskkit.backtest.compare import backtest, comparison_table, exceptions_table
from riskkit.backtest.traffic_light import rolling_zone

cfg = state.config()
kit.page_title("Backtesting", "Each evening's VaR, made with only the data known then, checked against the "
               "next day's actual loss. An <b>exception</b> is a day the loss beat the VaR.")
rollings = state.var_rolling(cfg)
first, last = rollings[cfg.var.model].index[0].date(), rollings[cfg.var.model].index[-1].date()


left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("bt_controls"):
    choice, view = controls.backtest_controls(cfg, first, last)
if isinstance(choice, str):
    left.error(choice)
elif any(getattr(cfg, k) != v for k, v in choice.items()):
    state.update_config(**choice)
    st.rerun()

start, sig, p = pd.Timestamp(view["start"]), view["significance"], 1 - cfg.confidence
window = {m: df.loc[start:] for m, df in rollings.items()}
bt = backtest(cfg.var.model, window[cfg.var.model], cfg.confidence, sig)
table = comparison_table(window, cfg.confidence, cfg.portfolio_value, sig)
state_of = {"green": "within", "yellow": "watch", "red": "breach"}

with right:
    kit.kpis([
        kit.Kpi("Exceptions", f"{bt.exceptions}", f"expected {bt.expected:.1f} in {bt.days:,} days"),
        kit.Kpi("Actual / expected", f"{bt.ratio:.2f}", "1.00 = perfect"),
        *[kit.Kpi(t.name, f"p = {t.p_value:.3f}", "pass" if t.passed else "fail", "within" if t.passed else "breach")
          for t in bt.tests],
        kit.Kpi("Basel zone", bt.zone_last_250.capitalize(), f"{bt.exceptions_last_250} in the last 250 days",
                state_of[bt.zone_last_250]),
    ])
    kit.checks({f"{c.name}: {c.detail}": c.passed for c in backtest_checks(bt)})
    kit.chart(rolling_chart(window, cfg.var.model, cfg.portfolio_value), "Actual P&L against VaR",
              f"Red dots: the {bt.exceptions} days the loss beat the {cfg.var.model} VaR.", key="pnl")
    kit.chart(charts.exception_timeline(window, cfg.var.model), "When the exceptions happened",
              "Clumps mean the model was surprised several times in a row: it reacted too slowly.", key="tl")
    with kit.panel("ranking"):
        best = table.iloc[0]
        kit.section("Model ranking", f"Best: <b>{best['model']}</b>. Passing every test first, then the exception "
                    "count closest to expected, then the lowest average VaR.")
        kit.table(table, [kit.Col("rank", "#", num=True), kit.Col("model", "Model"),
                          kit.Col("exceptions", "Exceptions", num=True), kit.Col("expected", "Expected", "{:.1f}", num=True),
                          kit.Col("ratio", "Ratio", "{:.2f}", num=True), kit.Col("average VaR", "Avg VaR", theme.money, num=True),
                          kit.Col("VaR volatility", "VaR jumpiness", theme.money, num=True),
                          kit.Col("worst daily loss", "Worst loss", theme.money, num=True),
                          kit.Col("average ES", "Avg ES", theme.money, num=True),
                          kit.Col("Kupiec p", "Kupiec p", kind="test", num=True),
                          kit.Col("Christoffersen p", "Christoffersen p", kind="test", num=True),
                          kit.Col("Coverage p", "Coverage p", kind="test", num=True),
                          kit.Col("zone", "Zone")], highlight=lambda r: r["model"] == cfg.var.model,
                  download="model_ranking")
        kit.note(f"Test columns show Pass when p ≥ 5%. Ranking uses your {sig:.0%} significance.")
    c1, c2 = st.columns(2)
    with c1:
        kit.chart(charts.exceptions_by_model(table), "Exceptions by model", key="bym")
    with c2:
        kit.chart(charts.traffic_light_chart(rolling_zone(bt.hits, 250, p), p), "Basel traffic light over time",
                  "Green 0–4, yellow 5–9, red 10+ exceptions in 250 days (at 99%).", key="traffic")
    with kit.panel("exc_table"):
        kit.section("Every exception", aside=cfg.var.model)
        kit.table(exceptions_table(window[cfg.var.model], cfg.portfolio_value),
                  [kit.Col("date", "Date", kit.day), kit.Col("var", "VaR that evening", theme.money, num=True),
                   kit.Col("loss", "Actual loss", theme.money, num=True),
                   kit.Col("excess", "Beaten by", theme.money, num=True)], height=320, download="exceptions")
