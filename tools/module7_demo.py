"""Module 7 demo: run every stress scenario on today's portfolio, print the ranking, save the slide chart.

Run from the V2 folder:  python -m tools.module7_demo          (online)
                         python -m tools.module7_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

import pandas as pd

from app.charts.stress import loss_chart
from riskkit.config import RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.portfolio.construction import build_portfolio
from riskkit.stress.engine import run_stress
from riskkit.var.engine import today_var

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def main() -> None:
    """Run, print and save."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    cd = clean_market_data(md, cfg)
    p = build_portfolio(cd, md, cfg)
    base = today_var(p.log_returns, cfg)
    s = run_stress(cfg, md, cd, p, base)
    cols = ["rank", "scenario", "kind", "loss_usd", "loss", "worst_day", "stressed_var"]
    with pd.option_context("display.width", 200, "display.float_format", "{:,.3f}".format):
        print(s.table[cols].to_string(index=False))
    print(f"\nToday's 1-day VaR {base.var_1d:.2%}; Basel stressed VaR {s.basel_svar:.2%} "
          f"(250 days ending {s.basel_svar_end:%d %b %Y}), {s.basel_svar / base.var_1d:.1f}x today")
    print("Betas:", s.betas.round(2).to_dict())
    try:
        loss_chart(s.table).update_layout(width=1000, height=520).write_image(OUT / "m7_scenarios.png", scale=2)
        print(f"Chart saved: {OUT / 'm7_scenarios.png'}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
