"""Compact previews and full CSV exports for the outputs produced on Page 2."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pandas as pd
import streamlit as st

from app.components import kit
from riskkit.data.pipeline import CleanData
from riskkit.portfolio.construction import Portfolio


@dataclass(frozen=True)
class OutputDataset:
    label: str
    frame: pd.DataFrame
    filename: str
    description: str
    percent: bool = False


def _dated_frame(data: pd.DataFrame | pd.Series) -> pd.DataFrame:
    """Return a download/display frame with its date index as the first column."""
    frame = data.to_frame() if isinstance(data, pd.Series) else data.copy()
    frame.index.name = frame.index.name or "Date"
    return frame.reset_index()


def _summary(frame: pd.DataFrame) -> str:
    dates = pd.to_datetime(frame.iloc[:, 0], errors="coerce").dropna()
    observations = len(frame)
    series = max(0, len(frame.columns) - 1)
    shape = f"{observations:,} dates · {series:,} series"
    if dates.empty:
        return shape
    return f"{shape} · {dates.iloc[0]:%d %b %Y}–{dates.iloc[-1]:%d %b %Y}"


def _csv(frame: pd.DataFrame) -> str:
    buffer = StringIO()
    frame.to_csv(buffer, index=False, date_format="%Y-%m-%d")
    return buffer.getvalue()


def _render_dataset(dataset: OutputDataset) -> None:
    frame = _dated_frame(dataset.frame)
    kit.note(f"{dataset.description}<br>{_summary(frame)}. Showing the latest 20 rows.")
    preview = frame.tail(20)
    numeric = list(preview.select_dtypes(include="number").columns)
    precision = "{:.4%}" if dataset.percent else "{:,.2f}"
    st.dataframe(
        preview.style.format({column: precision for column in numeric}),
        hide_index=True,
        width="stretch",
        height=min(420, 38 + 35 * (len(preview) + 1)),
    )
    st.download_button(
        "Download full CSV",
        _csv(frame),
        file_name=dataset.filename,
        mime="text/csv",
        key=f"download_{dataset.filename}",
    )


def render_data_outputs(
    clean_data: CleanData,
    portfolio_returns: pd.Series | None,
    rolling_vol: pd.DataFrame,
    *,
    return_type: str,
    rolling_window: int,
    portfolio_error: str | None = None,
) -> None:
    """Render the four Page 2 deliverables without crowding the main analysis."""
    with st.expander("Data outputs & downloads", expanded=False):
        kit.note("Inspect a recent sample here or export the complete dataset for audit and modelling.")
        price_tab, return_tab, portfolio_tab, volatility_tab = st.tabs(
            ["Clean prices", "Clean returns", "Portfolio returns", "Rolling volatility"]
        )

        with price_tab:
            _render_dataset(
                OutputDataset(
                    "Clean prices",
                    clean_data.prices,
                    "clean_price_matrix.csv",
                    "Split- and dividend-adjusted closing prices after date alignment, missing-value handling, and stale-price treatment.",
                )
            )

        with return_tab:
            _render_dataset(
                OutputDataset(
                    "Clean returns",
                    clean_data.returns,
                    "clean_return_matrix.csv",
                    f"Final {return_type} stock returns after the selected cleaning and outlier rules.",
                    percent=True,
                )
            )

        with portfolio_tab:
            if portfolio_returns is None:
                st.warning(f"Portfolio returns are unavailable with the current settings: {portfolio_error}")
            else:
                _render_dataset(
                    OutputDataset(
                        "Portfolio returns",
                        portfolio_returns.rename("Portfolio return"),
                        "portfolio_return_series.csv",
                        "Weighted daily simple returns using the portfolio construction settings on Page 3.",
                        percent=True,
                    )
                )

        with volatility_tab:
            _render_dataset(
                OutputDataset(
                    "Rolling volatility",
                    rolling_vol,
                    "rolling_volatility_series.csv",
                    f"Annualized stock volatility estimated from the trailing {rolling_window} trading days.",
                    percent=True,
                )
            )


def render_portfolio_outputs(portfolio: Portfolio) -> None:
    """Render full Page 3 output series behind a single compact disclosure."""
    with st.expander("Data outputs & downloads", expanded=False):
        kit.note("Inspect a recent sample here or export the complete portfolio history.")
        value_tab, pnl_tab, return_tab, weight_tab = st.tabs(
            ["Portfolio value", "Daily P&L", "Daily returns", "Portfolio weights"]
        )

        with value_tab:
            _render_dataset(
                OutputDataset(
                    "Portfolio value",
                    portfolio.value.rename("Portfolio value"),
                    "daily_portfolio_value.csv",
                    "Daily portfolio value in dollars, including the starting valuation date.",
                )
            )

        with pnl_tab:
            _render_dataset(
                OutputDataset(
                    "Daily P&L",
                    portfolio.pnl.rename("Daily P&L"),
                    "daily_portfolio_pnl.csv",
                    "Daily change in portfolio value after any rebalancing costs.",
                )
            )

        with return_tab:
            _render_dataset(
                OutputDataset(
                    "Daily returns",
                    portfolio.returns.rename("Portfolio return"),
                    "daily_portfolio_returns.csv",
                    "Daily simple portfolio returns used for performance reporting.",
                    percent=True,
                )
            )

        with weight_tab:
            _render_dataset(
                OutputDataset(
                    "Portfolio weights",
                    portfolio.weights,
                    "daily_portfolio_weights.csv",
                    "Actual closing weights, including drift between rebalance dates.",
                    percent=True,
                )
            )
