"""Module 5 demo: today's VaR/ES for the four models, the 3 x 3 grid, a quick breach count, slide charts.

Run from the V2 folder:  python -m tools.module5_demo          (online)
                         python -m tools.module5_demo offline  (saved prices only)
"""

import sys
from pathlib import Path

from app.charts.var import rolling_chart, scenario_histogram
from riskkit.config import VAR_MODELS, RiskConfig
from riskkit.data.collect import collect_market_data
from riskkit.data.pipeline import clean_market_data
from riskkit.portfolio.construction import build_portfolio
from riskkit.var.checks import var_checks
from riskkit.var.engine import all_models_today, confidence_window_grid, rolling_var

OUT = Path(__file__).resolve().parents[1] / "slides_assets"


def save(fig, name: str) -> None:
    """Write a chart for the slides (needs kaleido + Chrome)."""
    try:
        fig.write_image(OUT / name, scale=2)
        print(f"Chart saved: {OUT / name}")
    except Exception as exc:
        print(f"Chart not saved ({exc.__class__.__name__}): pip install kaleido, and have Chrome installed.")


def main() -> None:
    """Compute, print and save."""
    cfg = RiskConfig(offline="offline" in sys.argv)
    md = collect_market_data(cfg)
    r = build_portfolio(clean_market_data(md, cfg), md, cfg).log_returns
    results = all_models_today(r, cfg)
    for v in results:
        print(
            f"{v.model:9s} 1-day VaR ${v.var_1d_usd:>9,.0f} ({v.var_1d:.2%})  ES ${v.es_1d_usd:>9,.0f}  "
            f"10-day VaR ${v.var_h_usd:>11,.0f}"
        )
    print("\n", confidence_window_grid(r, cfg, cfg.var.model).map("{:.2%}".format).to_string(), sep="")
    rolling = {m: rolling_var(r, cfg, m) for m in VAR_MODELS}
    print()
    for m, df in rolling.items():
        n = int((df["actual"] > df["var"]).sum())
        print(f"{m:9s} losses beyond VaR: {n} of {len(df)} days ({n / len(df):.2%}, expected 1%)")
    for c in var_checks(r, cfg, results, rolling[cfg.var.model]):
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    gjr = next(v for v in results if v.model == "GJR-HS")
    save(scenario_histogram(gjr).update_layout(width=1000, height=500), "m5_scenarios.png")
    window = {m: rolling[m].loc["2020-01":"2020-12"] for m in ("HS", "GJR-HS")}
    fig = rolling_chart(window, "GJR-HS", cfg.portfolio_value)
    fig.update_traces(visible=True).update_layout(width=1000, height=500, legend=dict(y=1.08))
    fig.update_traces(selector=dict(name="Loss beyond VaR"), name="Loss beyond GJR-scaled VaR")
    hs = window["HS"]
    beyond = hs["actual"] > hs["var"]
    fig.add_scatter(
        x=hs.index[beyond],
        y=-hs["actual"][beyond] * cfg.portfolio_value,
        mode="markers",
        name="Loss beyond plain-history VaR",
        marker=dict(color="#161616", size=9, symbol="circle-open", line=dict(width=2)),
    )
    save(fig, "m5_rolling_2020.png")


if __name__ == "__main__":
    main()
