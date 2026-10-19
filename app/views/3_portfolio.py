"""Page 3, Portfolio (Module 3): how the money is split and what the basket did over time."""

import pandas as pd
import streamlit as st

from app import controls, state, theme
from app.charts import portfolio as charts
from app.components import kit
from riskkit.portfolio.drawdown import drawdown_episodes, drawdown_series
from riskkit.portfolio.performance import benchmark_comparison, benchmark_value, portfolio_checks, summary_stats

cfg = state.config()
kit.page_title("Portfolio", "The basket we hold: how the money is split, how it is managed, and what it was "
               "worth, gained and lost each day.")

left, right = st.columns([1, 2.7], gap="medium")
with left, kit.panel("pf_controls"):
    choice = controls.portfolio_controls(cfg)
if isinstance(choice, str):
    left.error(choice)
elif any(getattr(cfg, k) != v for k, v in choice.items()):
    state.update_config(**choice)
    st.rerun()

try:
    p = state.portfolio(cfg)
except ValueError as exc:
    right.error(str(exc))
    st.stop()
md = state.market_data(cfg)
s, b = summary_stats(p, md.risk_free), benchmark_comparison(p, md.benchmark)

with right:
    kit.kpis([
        kit.Kpi("Value", theme.money(s["end value"]), f"from {theme.money(s['start value'])} in {p.value.index[0]:%Y}"),
        kit.Kpi("Return per year", theme.pct(s["annual return"], 1), f"market {theme.pct(b['benchmark annual return'], 1)}"),
        kit.Kpi("Volatility per year", theme.pct(s["annual volatility"], 1), f"beta {b['beta']:.2f} to the market"),
        kit.Kpi("Sharpe ratio", f"{s['sharpe']:.2f}", "return per unit of risk"),
        kit.Kpi("Worst fall", theme.pct(s["max drawdown"], 1), f"worst day {theme.money(s['worst day $'])}", "watch"),
    ])
    kit.checks({f"{c.name}: {c.detail}": c.passed for c in portfolio_checks(p)})
    log_scale = st.toggle("Log scale", False, help="Equal steps = equal % growth; makes early years readable.")
    kit.chart(charts.value_chart(p.value, benchmark_value(md.benchmark, p.value).rename(cfg.benchmark), log_scale),
              "Portfolio value against the market",
              f"{theme.pct(s['annual return'], 1)} a year against {theme.pct(b['benchmark annual return'], 1)} for "
              f"{cfg.benchmark}, both starting from the same amount.", key="value")
    kit.chart(charts.drawdown_chart(drawdown_series(p.value)), "Drawdown: distance below the previous peak",
              f"The deepest fall was <b>{theme.pct(s['max drawdown'], 1)}</b>.", key="dd")
    in_pct = st.toggle("Daily results as % returns", False, help="Off: dollars of profit and loss. On: % return.")
    kit.chart(charts.returns_chart(p.returns) if in_pct else charts.pnl_chart(p.pnl),
              "Daily returns" if in_pct else "Daily profit and loss",
              f"Best day {theme.pct(p.returns.max())} ({theme.money(p.pnl.max())}), worst day "
              f"{theme.pct(p.returns.min())} ({theme.money(p.pnl.min())}); {s['positive days']:.0%} of days were gains.",
              key="pnl")
    kit.chart(charts.distribution_chart(p.returns), "Daily returns against a normal bell curve",
              "Real markets have more very big days than the bell curve predicts (\"fat tails\").", key="dist")
    kit.chart(charts.weights_chart(p.weights), "How the split drifts over time",
              f"Rebalancing: {controls.REBALANCE_LABELS[cfg.portfolio.rebalance].lower()}; "
              f"trading costs paid {theme.money(s['total costs'])}.", key="w")
    kit.chart(charts.contribution_chart(p.contributions.sum()), "Which stocks made the money", key="contrib")
    with kit.panel("pf_tables"):
        kit.section("Today's split")
        now = pd.DataFrame({"stock": p.current_weights.index, "target": p.targets.iloc[-1].values,
                            "held": p.current_weights.values, "pnl": p.contributions.sum().values})
        kit.table(now, [kit.Col("stock", "Stock"), kit.Col("target", "Target", theme.pct, num=True),
                        kit.Col("held", "Held now", theme.pct, num=True),
                        kit.Col("pnl", "Total P&L", theme.money, num=True)], download="portfolio_weights")
        kit.section("Worst falls", aside="peak to recovery")
        kit.table(drawdown_episodes(p.value), [kit.Col("peak", "Peak", kit.day), kit.Col("trough", "Bottom", kit.day),
                  kit.Col("recovery", "Recovered", kit.day), kit.Col("depth", "Depth", theme.pct, num=True),
                  kit.Col("days_down", "Days falling", "{:,}", num=True),
                  kit.Col("days_to_recover", "Days to recover", "{:,.0f}", num=True)])
