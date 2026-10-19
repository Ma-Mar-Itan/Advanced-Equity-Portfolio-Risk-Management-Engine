"""Module 3 demo: build the default portfolio, compare weighting schemes, save the slide chart.

Run from the V2 folder:  python -m tools.module3_demo          (online)
                         python -m tools.module3_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

import pandas as pd

from app.charts.portfolio import drawdown_chart
from riskkit.config import PortfolioSpec, RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.portfolio.construction import build_portfolio
from riskkit.portfolio.drawdown import drawdown_episodes, drawdown_series
from riskkit.portfolio.performance import benchmark_comparison, portfolio_checks, summary_stats

OUT = Path(__file__).resolve().parents[1] / "slides_assets"
SCHEMES = {"Equal, monthly": PortfolioSpec(), "Equal, buy and hold": PortfolioSpec(rebalance="none"),
           "By company size": PortfolioSpec(scheme="market_cap"), "By calmness": PortfolioSpec(scheme="inverse_vol")}


def main() -> None:
    """Print a comparison of weighting schemes and the default portfolio's worst falls; save the chart."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    cd = clean_market_data(md, cfg)
    rows = {}
    for name, spec in SCHEMES.items():
        p = build_portfolio(cd, md, cfg.updated(portfolio=spec))
        s = summary_stats(p, md.risk_free)
        rows[name] = {"return/yr": f"{s['annual return']:.1%}", "volatility/yr": f"{s['annual volatility']:.1%}",
                      "sharpe": f"{s['sharpe']:.2f}", "worst fall": f"{s['max drawdown']:.1%}"}
    print(pd.DataFrame(rows).T.to_string())
    p = build_portfolio(cd, md, cfg)
    b = benchmark_comparison(p, md.benchmark)
    print(f"\nMarket ({cfg.benchmark}): {b['benchmark annual return']:.1%} a year; portfolio beta {b['beta']:.2f}")
    for c in portfolio_checks(p):
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    print("\nWorst falls:\n", drawdown_episodes(p.value).to_string())
    fig = drawdown_chart(drawdown_series(p.value)).update_layout(width=1000, height=500)
    try:
        fig.write_image(OUT / "m3_drawdown.png", scale=2)
        print(f"\nChart saved: {OUT / 'm3_drawdown.png'}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
