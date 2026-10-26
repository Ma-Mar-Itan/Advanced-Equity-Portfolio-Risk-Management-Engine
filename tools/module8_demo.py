"""Module 8 demo: where the risk comes from, a what-if trade, the best hedges and the optimizer.

Run from the V2 folder:  python -m tools.module8_demo          (online)
                         python -m tools.module8_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

import pandas as pd

from app.charts.extras import share_chart
from riskkit.attribution.euler import active_risk, attribution_table, diversification
from riskkit.attribution.scenarios import build_scenarios
from riskkit.config import RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.decisions.hedge import best_hedges
from riskkit.decisions.optimize import compare_splits, min_es_weights
from riskkit.decisions.whatif import what_if
from riskkit.portfolio.construction import build_portfolio, simple_asset_returns

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def main() -> None:
    """Compute, print and save."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    cd = clean_market_data(md, cfg)
    p = build_portfolio(cd, md, cfg)
    sc = build_scenarios(cd, md, p, cfg)
    sectors = pd.Series({t: md.profiles[t].sector for t in sc.weights.index})
    t = attribution_table(sc, sectors)
    with pd.option_context("display.width", 200, "display.float_format", "{:,.3f}".format):
        print(t[["stock", "weight", "es_share", "var_share", "es_usd"]].to_string(index=False))
    d, a = diversification(sc), active_risk(sc, p.returns, md.benchmark)
    print(
        f"\nVaR ${d['var']:,.0f}; stand-alone sum ${d['sum_standalone']:,.0f}; saved by mixing "
        f"${d['benefit']:,.0f} ({d['benefit_share']:.0%}); tracking error {a['tracking error']:.1%}"
    )
    w = what_if(sc, "AAPL", 1_000_000, "pro_rata")
    print(f"What-if +$1M AAPL (pro rata): VaR ${w['var_before']:,.0f} -> ${w['var_after']:,.0f}")
    h = best_hedges(sc, cfg.benchmark)
    print("\n", h.head(4).to_string(index=False), sep="")
    new = min_es_weights(sc, 0.25)
    print("\nMin-ES weights (cap 25%):", new[new > 0.001].round(3).to_dict())
    print(compare_splits(sc, new, simple_asset_returns(cd, cfg.cleaning.return_type)).to_string(index=False))
    try:
        share_chart(t, "ES").update_layout(width=1000, height=500).write_image(OUT / "m8_risk_share.png", scale=2)
        print(f"Chart saved: {OUT / 'm8_risk_share.png'}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
