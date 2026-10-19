"""Module 1 demo: collect the default portfolio's data, print a summary, save the growth chart.

Run from the V2 folder:  python -m tools.module1_demo          (online)
                         python -m tools.module1_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

import pandas as pd

from app.charts.data import growth_chart, growth_of_one_dollar
from riskkit.config import RiskConfig
from riskkit.data.collect import collect_market_data, summary_table

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def main() -> None:
    """Collect data, print the summary and save the chart for the slides."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    prices = md.prices.loc[pd.Timestamp(cfg.start):]
    print(f"Stocks loaded: {len(prices.columns)}   failed: {list(md.failed) or 'none'}")
    print(f"Dates: {prices.index.min().date()} to {md.as_of.date()}   ({len(prices)} trading days)")
    print(f"Benchmark: {cfg.benchmark} ({md.origin[cfg.benchmark]})   Risk-free: {md.origin['risk-free']}")
    print(f"Latest risk-free rate: {md.risk_free.iloc[-1] * 252:.2%} a year\n")
    with pd.option_context("display.width", 160):
        print(summary_table(md, cfg).to_string())
    growth = growth_of_one_dollar(prices)
    print("\n$1 invested at the start is now worth:")
    print(growth.iloc[-1].sort_values(ascending=False).map("${:,.2f}".format).to_string())
    OUT.mkdir(exist_ok=True)
    try:
        growth_chart(growth).update_layout(width=1000, height=560).write_image(OUT / "m1_growth_of_1_dollar.png", scale=2)
        print(f"\nChart saved: {OUT / 'm1_growth_of_1_dollar.png'}")
    except Exception as exc:  # kaleido or Chrome missing: the data part still worked
        print(f"\nChart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
