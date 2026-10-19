"""Module 4 demo: fit the four volatility models to the portfolio, print the key numbers, save slide charts.

Run from the V2 folder:  python -m tools.module4_demo          (online)
                         python -m tools.module4_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

from app.charts.volatility import clustering_chart, leverage_chart
from riskkit.config import RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.portfolio.construction import build_portfolio
from riskkit.volatility.analysis import fit_all, leverage_effect, regime_table, volatility_regimes
from riskkit.volatility.base import annualize

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def save(fig, name: str) -> None:
    """Write a chart for the slides (needs kaleido + Chrome)."""
    try:
        fig.write_image(OUT / name, scale=2)
        print(f"Chart saved: {OUT / name}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


def main() -> None:
    """Fit, print and save."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    r = build_portfolio(clean_market_data(md, cfg), md, cfg).log_returns
    fits = fit_all(r, cfg.volatility)
    for name, f in fits.items():
        print(f"{name:12s} today {annualize(f.next_day):6.1%} a year   in 10 days {annualize(f.forecast[-1]):6.1%}")
    g = fits["GJR-GARCH"].params
    print(f"\nGJR: alpha {g['alpha']:.3f}  gamma {g['gamma']:.3f}  beta {g['beta']:.3f}  "
          f"long-run {g['long-run vol (yearly)']:.1%}  half-life {g['half-life (days)']:.0f} days")
    z = fits["GJR-GARCH"].std_residuals(r)
    print(f"Kurtosis (normal = 3): raw {r.kurt() + 3:.1f}, after GJR {z.kurt() + 3:.1f}")
    print("\n", regime_table(r, volatility_regimes(fits["GJR-GARCH"].sigma)).to_string(), sep="")
    lev = leverage_effect(r)
    print("\n", lev.to_string(), sep="")
    window = r.loc["2019-06":"2021-06"]
    save(clustering_chart(window, fits["GJR-GARCH"]).update_layout(width=1000, height=500), "m4_clustering.png")
    save(leverage_chart(lev).update_layout(width=1000, height=500), "m4_leverage.png")


if __name__ == "__main__":
    main()
