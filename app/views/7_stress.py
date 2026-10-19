"""Page 7, Stress testing (Module 7): what if a crisis happened tomorrow?"""

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import stress as charts
from app.components import kit
from riskkit.stress.engine import by_sector

cfg = state.config()
kit.page_title("Stress testing", "Real crises replayed on the portfolio we hold <i>today</i>, and made-up shocks: "
               "the days VaR is not built for.")
md = state.market_data(cfg)
sectors = pd.Series({t: md.profiles[t].sector for t in md.prices.columns})

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("st_controls"):
    spec = controls.stress_controls(cfg, sorted(sectors.unique()))
if isinstance(spec, str):
    left.error(spec)
elif spec != cfg.stress:
    state.update_config(stress=spec)
    st.rerun()

s = state.stress(cfg)
base = next(r for r in state.var_today(cfg) if r.model == cfg.var.model)
worst = s.table.iloc[0]

with right:
    kit.kpis([
        kit.Kpi("Worst scenario", theme.money(worst["loss_usd"]), f"{worst['scenario']}: {theme.pct(worst['loss'], 1)}",
                "breach"),
        kit.Kpi(f"Today's 1-day VaR", theme.money(base.var_1d_usd), cfg.var.model),
        kit.Kpi("Stressed VaR (Basel)", theme.money(s.basel_svar * s.value),
                f"worst 250 days, ending {s.basel_svar_end:%b %Y}", "watch"),
        kit.Kpi("Stressed / today", f"{s.basel_svar / base.var_1d:.1f}×", "how much worse a crisis year is"),
    ])
    kit.chart(charts.loss_chart(s.table), "Scenario ranking: loss on today's portfolio",
              "Teal: real crises replayed. Grey: made-up shocks. Negative = the portfolio would have gained.", key="loss")
    with kit.panel("st_table"):
        kit.section("Every scenario", aside="worst first")
        kit.table(s.table, [kit.Col("rank", "#", num=True), kit.Col("scenario", "Scenario"), kit.Col("kind", "Type", dim=True),
                            kit.Col("loss_usd", "Loss", theme.money, num=True), kit.Col("loss", "% of value", theme.pct, num=True),
                            kit.Col("worst_day", "Worst day", theme.pct, num=True),
                            kit.Col("stressed_var", "Stressed VaR", theme.pct, num=True),
                            kit.Col("stressed_es", "Stressed ES", theme.pct, num=True), kit.Col("note", "Note", dim=True)],
                  download="stress_results")
    kit.chart(charts.stressed_var_chart(s.table, base.var_1d_usd, s.basel_svar * s.value, s.value),
              "Stressed VaR against today's VaR",
              "Historical rows: VaR if the next day came from the year ending with the crisis.", key="svar")
    pick = st.selectbox("Look inside a scenario", list(s.table["scenario"]))
    losses_usd = s.by_stock[pick] * s.value
    c1, c2 = st.columns(2)
    with c1:
        kit.chart(charts.contribution_chart(losses_usd), f"{pick}: loss by stock", key="bystock")
    with c2:
        kit.chart(charts.contribution_chart(by_sector(losses_usd, sectors)), f"{pick}: loss by sector", key="bysec")
    if pick in s.replays:
        rep = s.replays[pick]
        kit.chart(charts.path_chart(rep.path, s.value), f"{pick}, replayed from tomorrow",
                  f"Total {theme.pct(-rep.loss, 1)}, deepest fall {theme.pct(-rep.max_drawdown, 1)}, worst day "
                  f"{theme.pct(-rep.worst_day, 1)}." + (f" Stand-ins: {', '.join(rep.proxied)} (beta × market)."
                                                        if rep.proxied else ""), key="path")
