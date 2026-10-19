"""Best single hedge: which one position cuts VaR the most, and how big should it be?

A hedge is a position that tends to gain when the portfolio loses (like insurance). For each
candidate (shorting any one stock, or the benchmark), try every size from 0 to 200% of the
portfolio value and keep the one with the lowest VaR.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from riskkit.attribution.scenarios import Scenarios, var_es_simple


def hedge_candidates(sc: Scenarios, benchmark_name: str) -> pd.DataFrame:
    """Scenario returns of every possible hedge instrument: each stock and the benchmark."""
    out = sc.assets.copy()
    out[benchmark_name] = sc.benchmark
    return out


def best_size(port: np.ndarray, hedge: np.ndarray, confidence: float, sizes: np.ndarray) -> tuple[float, float]:
    """The hedge size (share of value, negative = short) with the lowest VaR, and that VaR."""
    vars_ = [var_es_simple(pd.Series(port + h * hedge), confidence)[0] for h in sizes]
    i = int(np.argmin(vars_))
    return float(sizes[i]), float(vars_[i])


def best_hedges(sc: Scenarios, benchmark_name: str, max_size: float = 2.0, steps: int = 201) -> pd.DataFrame:
    """For each instrument: best hedge size, its dollar amount, VaR after, and the VaR reduction. Best first."""
    port = sc.portfolio().to_numpy()
    base = var_es_simple(sc.portfolio(), sc.confidence)[0]
    sizes = np.linspace(-max_size, 0.0, steps)
    rows = []
    for name, r in hedge_candidates(sc, benchmark_name).items():
        size, var = best_size(port, r.to_numpy(), sc.confidence, sizes)
        rows.append({"instrument": name, "size": size, "amount": size * sc.value, "var_before": base * sc.value,
                     "var_after": var * sc.value, "reduction": 1 - var / base})
    return pd.DataFrame(rows).sort_values("reduction", ascending=False).reset_index(drop=True)
