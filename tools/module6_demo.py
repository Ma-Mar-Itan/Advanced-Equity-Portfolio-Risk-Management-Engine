"""Module 6 demo: backtest the four VaR models, print the ranking, save the slide chart.

Run from the V2 folder:  python -m tools.module6_demo          (online)
                         python -m tools.module6_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

import pandas as pd

from app.charts.backtest import exception_timeline
from riskkit.backtest.compare import comparison_table
from riskkit.config import VAR_MODELS, RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.portfolio.construction import build_portfolio
from riskkit.var.engine import rolling_var

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def main() -> None:
    """Backtest at 95% and 99%, print the ranking tables, save the exception timeline."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    r = build_portfolio(clean_market_data(md, cfg), md, cfg).log_returns
    for c in (0.99, 0.95):
        rollings = {m: rolling_var(r, cfg, m, c) for m in VAR_MODELS}
        t = comparison_table(rollings, c, cfg.portfolio_value)
        cols = [
            "rank",
            "model",
            "exceptions",
            "expected",
            "Kupiec p",
            "Christoffersen p",
            "Coverage p",
            "zone",
            "average VaR",
            "passes all",
        ]
        print(f"\n{c:.0%} VaR, {t.loc[0, 'expected']:.0f} exceptions expected over {len(rollings['HS']):,} days")
        with pd.option_context("display.width", 200, "display.float_format", "{:,.3f}".format):
            print(t[cols].to_string(index=False))
        if c == 0.99:
            keep = {m: rollings[m] for m in ("HS", "GJR-HS")}
            fig = exception_timeline(keep, "GJR-HS").update_layout(width=1000, height=320, margin=dict(l=80))
            try:
                fig.write_image(OUT / "m6_exception_timeline.png", scale=2)
                print(f"Chart saved: {OUT / 'm6_exception_timeline.png'}")
            except Exception as exc:
                print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
