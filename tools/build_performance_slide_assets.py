"""Build the charts used by the final simulated-performance slide."""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from riskkit.portfolio.construction import simulate
from riskkit.portfolio.drawdown import drawdown_series
from riskkit.portfolio.weights import rebalance_dates


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "slides_assets" / "performance"
def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tickers = ["AAPL", "MSFT", "NVDA", "JPM", "XOM", "AMZN", "META", "GOOGL", "TSLA", "UNH"]
    prices = pd.concat(
        {
            ticker: pd.read_parquet(ROOT / "data" / "snapshot" / "yahoo" / f"{ticker}.parquet")["adj_close"]
            for ticker in tickers
        },
        axis=1,
        join="inner",
    ).loc["2012-06-01":]
    asset_returns = prices.pct_change().dropna()
    start_date = prices.index[prices.index < asset_returns.index[0]][-1]
    dates = pd.DatetimeIndex([start_date]).append(rebalance_dates(asset_returns.index, "monthly"))
    targets = pd.DataFrame(0.1, index=dates, columns=tickers)
    raw = simulate(asset_returns, targets, 0.0, start_date)
    value = raw["value"] * 10_000_000
    contributions = raw["contributions"] * 10_000_000

    contribution = contributions.sum().sort_values(ascending=False) / 1_000_000
    dd = drawdown_series(value) * 100
    trough = pd.Timestamp(dd.idxmin())
    monthly_value = value.resample("MS").last()
    monthly_drawdown = dd.resample("MS").min()
    payload = {
        "start": float(value.iloc[0]),
        "end": float(value.iloc[-1]),
        "profit": float(value.iloc[-1] - value.iloc[0]),
        "growth_dates": [f"{date:%Y-%m}" for date in monthly_value.index],
        "growth_millions": [round(float(item / 1_000_000), 4) for item in monthly_value],
        "drawdown_dates": [f"{date:%Y-%m}" for date in monthly_drawdown.index],
        "drawdown_pct": [round(float(item), 4) for item in monthly_drawdown],
        "worst_drawdown_date": f"{trough:%d %B %Y}",
        "worst_drawdown_pct": float(dd.min()),
        "contribution_names": contribution.index.tolist(),
        "contribution_millions": [round(float(item), 4) for item in contribution],
    }
    (OUTPUT / "performance_data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Start: ${value.iloc[0]:,.0f}")
    print(f"End: ${value.iloc[-1]:,.0f}")
    print(f"Profit: ${value.iloc[-1] - value.iloc[0]:,.0f}")
    print(contribution.to_string())


if __name__ == "__main__":
    main()
