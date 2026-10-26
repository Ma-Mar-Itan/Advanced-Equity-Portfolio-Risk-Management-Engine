import pandas as pd
import plotly.graph_objects as go

from app.components.data_outputs import _csv, _dated_frame, _summary
from app.components.kit import chart_frame, ensure_chart_legend


def test_output_frame_preserves_dates_and_series() -> None:
    dates = pd.date_range("2025-01-02", periods=2, name="Trading date")
    source = pd.DataFrame({"AAA": [100.0, 101.5], "BBB": [50.0, 49.0]}, index=dates)

    output = _dated_frame(source)

    assert list(output.columns) == ["Trading date", "AAA", "BBB"]
    assert _summary(output) == "2 dates · 2 series · 02 Jan 2025–03 Jan 2025"


def test_output_csv_uses_iso_dates_and_no_dataframe_index() -> None:
    source = pd.Series([0.01], index=pd.to_datetime(["2025-01-02"]), name="Portfolio return")
    output = _dated_frame(source)

    csv = _csv(output)

    assert csv.splitlines() == ["Date,Portfolio return", "2025-01-02,0.01"]


def test_chart_frame_exports_every_trace_in_long_form() -> None:
    figure = go.Figure()
    figure.add_scatter(x=pd.to_datetime(["2025-01-02", "2025-01-03"]), y=[1.0, 2.0], name="Value")
    figure.add_histogram(x=[-0.1, 0.2], name="Returns")

    output = chart_frame(figure)

    assert list(output.columns) == ["series", "chart_type", "x", "y"]
    assert output["series"].tolist() == ["Value", "Value", "Returns", "Returns"]
    assert output["chart_type"].tolist() == ["scatter", "scatter", "histogram", "histogram"]
    assert output.loc[2:, "y"].isna().all()


def test_chart_legend_fallback_names_an_unlabelled_series() -> None:
    figure = go.Figure(go.Bar(x=["A"], y=[1.0]))

    ensure_chart_legend(figure, "Example result")

    assert figure.layout.showlegend is True
    assert figure.data[0].name == "Example result"
    assert figure.layout.legend.orientation == "h"
