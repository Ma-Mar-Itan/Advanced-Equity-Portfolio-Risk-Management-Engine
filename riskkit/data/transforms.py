"""Optional return transformations, including winsorization and custom formulas.

Winsorization limits extreme observations but can suppress genuine tail events.
It is therefore disabled by default.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.data.cleaning import empty_log, log_from_mask


def winsor_bounds(
    r: pd.DataFrame, method: str, lower: float = 0.001, upper: float = 0.999, k: float = 6.0, cap: float = 0.25
) -> tuple[pd.Series, pd.Series]:
    """Per-stock floor and ceiling for each winsorizing method.

    quantile - the `lower` and `upper` percentiles of each stock's own history
    sigma    - mean +/- k standard deviations
    cap      - a fixed -cap / +cap for every stock
    """
    if method == "quantile":
        return r.quantile(lower), r.quantile(upper)
    if method == "sigma":
        return r.mean() - k * r.std(), r.mean() + k * r.std()
    if method == "cap":
        return pd.Series(-cap, index=r.columns), pd.Series(cap, index=r.columns)
    raise ValueError(f"Unknown winsorizing method '{method}'.")


def winsorize(r: pd.DataFrame, method: str, **params: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clip each stock's returns to its bounds; returns the clipped table and a log of what moved."""
    if method == "none":
        return r, empty_log()
    low, high = winsor_bounds(r, method, **params)
    clipped = r.clip(lower=low, upper=high, axis=1)
    log = log_from_mask(clipped.ne(r) & r.notna(), "winsorize", f"return clipped ({method})")
    return clipped, log


#: Functions a custom formula may use. `r` is the table of returns (dates x stocks).
SAFE_FUNCTIONS = {
    "np": np,
    "abs": np.abs,
    "sqrt": np.sqrt,
    "log": np.log,
    "log1p": np.log1p,
    "exp": np.exp,
    "sign": np.sign,
    "clip": lambda x, lo, hi: x.clip(lo, hi),
    "mean": lambda x: x.mean(),
    "median": lambda x: x.median(),
    "std": lambda x: x.std(),
    "rolling_mean": lambda x, n: x.rolling(int(n)).mean(),
    "rolling_std": lambda x, n: x.rolling(int(n)).std(),
    "lag": lambda x, n=1: x.shift(int(n)),
    "where": lambda cond, a, b: a.where(cond, b),
}


def apply_custom_expression(r: pd.DataFrame, expression: str) -> pd.DataFrame:
    """Apply a formula typed by the user to the returns table `r`, e.g. 'clip(r, -0.2, 0.2)'.

    Only `r` and the names in SAFE_FUNCTIONS are available. The result must be a table
    of the same shape; rows left empty by rolling windows are dropped.
    """
    expression = expression.strip()
    if not expression:
        return r
    if "__" in expression or "import" in expression:
        raise ValueError("That formula uses something that is not allowed.")
    try:
        out = eval(expression, {"__builtins__": {}}, {**SAFE_FUNCTIONS, "r": r})  # noqa: S307 - restricted names
    except Exception as exc:
        raise ValueError(f"Formula failed: {exc}") from exc
    if not isinstance(out, pd.DataFrame) or list(out.columns) != list(r.columns):
        raise ValueError("The formula must return a table with one column per stock (use `r` in it).")
    out = out.replace([np.inf, -np.inf], np.nan).dropna(how="any")
    if out.empty:
        raise ValueError("The formula left no usable rows.")
    return out
