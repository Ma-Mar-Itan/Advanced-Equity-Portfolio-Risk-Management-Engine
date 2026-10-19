"""Module 2 demo: clean the default portfolio, print the checks, save the slide chart.

Run from the V2 folder:  python -m tools.module2_demo          (online)
                         python -m tools.module2_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

from app.charts.cleaning import returns_timeline
from riskkit.config import CleaningSpec, RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data

OUT = Path(__file__).resolve().parents[1] / "slides_assets"
STOCK = "AAPL"


def main() -> None:
    """Clean with the defaults, then show what 1%/99% winsorizing would have changed."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    cd = clean_market_data(md, cfg)
    print(f"Days kept: {len(cd.returns):,}   filled: {cd.count('fill')}   stale: {cd.count('stale')}")
    for c in cd.checks:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    clipped = clean_market_data(md, cfg.updated(cleaning=CleaningSpec(winsor_method="quantile",
                                                                      winsor_lower=0.01, winsor_upper=0.99)))
    days = clipped.log[clipped.log["ticker"] == STOCK]["date"]
    print(f"\n1%/99% winsorizing would change {clipped.count('winsorize')} returns in total, "
          f"{len(days)} of them for {STOCK}; busiest year: {days.dt.year.value_counts().idxmax()}")
    fig = returns_timeline(clipped.raw_returns[STOCK], clipped.returns[STOCK])
    fig.update_layout(width=1000, height=520, legend=dict(y=1.02))
    try:
        fig.write_image(OUT / "m2_winsorizing_hides_crashes.png", scale=2)
        print(f"Chart saved: {OUT / 'm2_winsorizing_hides_crashes.png'}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


if __name__ == "__main__":
    main()
