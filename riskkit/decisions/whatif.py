"""Pre-trade what-if: how would a trade change VaR and ES, before we make it?"""

from __future__ import annotations

import pandas as pd

from riskkit.attribution.scenarios import Scenarios, var_es_simple


def trade_weights(weights: pd.Series, value: float, ticker: str, amount: float, funding: str) -> tuple[pd.Series, float]:
    """New weights and value after buying (amount > 0) or selling (amount < 0) `amount` dollars of `ticker`.

    funding='cash'     - new money comes in (or goes out): the portfolio grows (or shrinks)
    funding='pro_rata' - the trade is paid for by selling (or buying) a bit of every other stock: value unchanged
    """
    dollars = weights * value
    if funding == "cash":
        dollars[ticker] += amount
        new_value = value + amount
    else:
        others = dollars.drop(ticker)
        dollars[ticker] += amount
        dollars[others.index] -= amount * others / others.sum()
        new_value = value
    if new_value <= 0:
        raise ValueError("That trade would leave nothing in the portfolio.")
    return dollars / new_value, new_value


def what_if(sc: Scenarios, ticker: str, amount: float, funding: str) -> dict[str, object]:
    """VaR and ES in dollars before and after the trade, plus the new weights."""
    before_var, before_es = var_es_simple(sc.portfolio(), sc.confidence)
    w, v = trade_weights(sc.weights.copy(), sc.value, ticker, amount, funding)
    after_var, after_es = var_es_simple(sc.portfolio(w), sc.confidence)
    return {"weights_before": sc.weights, "weights_after": w, "value_after": v,
            "var_before": before_var * sc.value, "var_after": after_var * v,
            "es_before": before_es * sc.value, "es_after": after_es * v}
