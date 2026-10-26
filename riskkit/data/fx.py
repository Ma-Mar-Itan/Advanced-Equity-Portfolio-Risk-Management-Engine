"""Convert prices quoted in other currencies into the portfolio's currency (USD).

A Swiss stock priced at 100 francs is worth 100 x (dollars per franc) dollars.
Yahoo quotes that exchange rate as the ticker 'CHFUSD=X'.
Some London, Johannesburg and Tel Aviv stocks are quoted in pennies / cents /
agorot, so those prices are first divided by 100.
"""

from __future__ import annotations

import pandas as pd

#: Currencies quoted in hundredths: code -> (main currency, divisor)
MINOR_UNITS: dict[str, tuple[str, int]] = {
    "GBp": ("GBP", 100),
    "GBX": ("GBP", 100),
    "ZAc": ("ZAR", 100),
    "ILA": ("ILS", 100),
}


def major_currency(code: str) -> tuple[str, int]:
    """Main currency and divisor for a quote currency: 'GBp' -> ('GBP', 100), 'EUR' -> ('EUR', 1)."""
    return MINOR_UNITS.get(code, (code.upper(), 1))


def fx_ticker(currency: str, base: str = "USD") -> str:
    """Yahoo ticker for the price of one unit of `currency` in `base`, e.g. 'EURUSD=X'."""
    return f"{currency}{base}=X"


def needs_conversion(code: str, base: str = "USD") -> bool:
    """True when a quote currency is not already the base currency."""
    major, divisor = major_currency(code)
    return major != base or divisor != 1


def convert_prices(prices: pd.Series, fx_rate: pd.Series | None, divisor: int = 1) -> pd.Series:
    """Prices in the base currency: price / divisor x the exchange rate known on that day.

    fx_rate=None means the main currency is already the base (only the divisor applies).
    The exchange rate is carried forward over days the FX market had no quote.
    """
    out = prices / divisor
    if fx_rate is None:
        return out
    rate = fx_rate.reindex(out.index.union(fx_rate.index)).ffill().reindex(out.index)
    return out * rate
