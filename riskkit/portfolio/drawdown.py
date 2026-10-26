"""Drawdown: how far the portfolio is below its best value so far.

Worth $12M at its peak and $9M now -> drawdown of -25%. It answers "how bad did it feel?".
"""

from __future__ import annotations

import pandas as pd


def drawdown_series(value: pd.Series) -> pd.Series:
    """Each day's fall from the highest value reached up to that day (0 at a new high, negative below)."""
    return value / value.cummax() - 1


def max_drawdown(value: pd.Series) -> float:
    """The deepest fall from a peak over the whole history (a negative number)."""
    return float(drawdown_series(value).min())


def drawdown_episodes(value: pd.Series, top: int = 5) -> pd.DataFrame:
    """The `top` deepest falls: when each started (peak), bottomed (trough) and recovered.

    Columns: peak, trough, recovery (NaT if not yet recovered), depth, days_down, days_to_recover.
    """
    dd = drawdown_series(value)
    underwater = dd < 0
    episode_id = (~underwater).cumsum()[underwater]  # one id per stretch below the peak
    rows = []
    for _, days in dd[underwater].groupby(episode_id):
        peak = value.index[value.index.get_loc(days.index[0]) - 1]
        trough = days.idxmin()
        after = value.index.get_loc(days.index[-1]) + 1
        recovery = value.index[after] if after < len(value) else pd.NaT
        rows.append(
            {
                "peak": peak,
                "trough": trough,
                "recovery": recovery,
                "depth": float(days.min()),
                "days_down": int(value.index.get_loc(trough) - value.index.get_loc(peak)),
                "days_to_recover": (int(after - value.index.get_loc(trough)) if recovery is not pd.NaT else None),
            }
        )
    table = pd.DataFrame(rows, columns=["peak", "trough", "recovery", "depth", "days_down", "days_to_recover"])
    return table.sort_values("depth").head(top).reset_index(drop=True)
