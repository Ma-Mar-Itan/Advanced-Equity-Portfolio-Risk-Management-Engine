"""The library of historical crises (dates are peak-to-trough of the relevant market)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class HistoricalScenario:
    """A real crisis window to replay on today's portfolio."""

    name: str
    start: str
    end: str
    story: str

    @property
    def dates(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Start and end as timestamps."""
        return pd.Timestamp(self.start), pd.Timestamp(self.end)


LIBRARY: dict[str, HistoricalScenario] = {
    s.name: s
    for s in [
        HistoricalScenario("2008 financial crisis", "2008-09-01", "2009-03-09", "Lehman collapse to the market bottom"),
        HistoricalScenario("COVID crash 2020", "2020-02-19", "2020-03-23", "Pandemic: fastest 30% fall on record"),
        HistoricalScenario("Inflation shock 2022", "2022-01-03", "2022-10-12", "Rate hikes: S&P 500 peak to trough"),
        HistoricalScenario("Banking stress 2023", "2023-03-08", "2023-03-17", "Silicon Valley Bank failure"),
        HistoricalScenario("Tech selloff 2021-22", "2021-11-19", "2022-12-28", "Nasdaq peak to trough"),
        HistoricalScenario("Tariff shock April 2025", "2025-04-02", "2025-04-08", "US tariff announcement selloff"),
    ]
}
