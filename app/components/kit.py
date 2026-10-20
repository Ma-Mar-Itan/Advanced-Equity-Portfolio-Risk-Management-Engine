"""Design-system components rendered as HTML (no JavaScript).

Every visual element the pages use beyond plain Streamlit widgets lives here, so the
look is defined in one place: page titles, the headline VaR with its limit rail, KPI
strips, section headings, status dots, panels and dense HTML tables.
"""

from __future__ import annotations

import html
import io
import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import theme

_CSS = (Path(__file__).resolve().parents[1] / "assets" / "style.css").read_text(encoding="utf-8")
_counter = itertools.count()


def esc(x: object) -> str:
    return html.escape(str(x))


def inject_css() -> None:
    st.html(f"<style>{_CSS}</style>")


def render(markup: str) -> None:
    st.html(markup)


# --------------------------------------------------------------------------- state
def state_of_zone(zone: str | None) -> str:
    return {"green": "within", "yellow": "watch", "red": "breach"}.get((zone or "").lower(), "neutral")


def state_of_use(use: float) -> str:
    return "within" if use < 0.8 else ("watch" if use <= 1.0 else "breach")


def dot(state: str) -> str:
    return f'<span class="rk-dot bg-{state}"></span>'


def status(state: str, text: str) -> str:
    return f'{dot(state)}<span class="rk-state-{state}">{esc(text)}</span>'


# --------------------------------------------------------------------------- headings
def page_title(title: str, lede: str | None = None) -> None:
    """Page heading. ``lede`` is trusted HTML: one or two sentences stating what the page finds."""
    lede_html = f"<p>{lede}</p>" if lede else ""
    render(f'<div class="rk-title"><h1>{esc(title)}</h1>{lede_html}</div>')


def part(title: str, lede: str | None = None) -> None:
    """A heading that starts a new part of a page (trusted HTML lede)."""
    lede_html = f"<p>{lede}</p>" if lede else ""
    render(f'<div class="rk-part"><h2>{esc(title)}</h2>{lede_html}</div>')


def section(title: str, finding: str | None = None, aside: str | None = None) -> None:
    aside_html = f'<span class="rk-sec-aside">{esc(aside)}</span>' if aside else ""
    finding_html = f'<div class="rk-sec-finding">{finding}</div>' if finding else ""
    render(f'<div class="rk-sec"><h3>{esc(title)}</h3>{aside_html}</div>{finding_html}')


def note(text: str) -> None:
    render(f'<div class="rk-note">{text}</div>')


def para(text: str) -> None:
    """A sentence or two of body copy inside a panel (trusted HTML)."""
    render(f'<div class="rk-para">{text}</div>')


def flag(text: str, state: str = "watch") -> None:
    """A one-line status message (no box, no icon): a coloured dot and plain text."""
    render(f'<div class="rk-flagline">{dot(state)}{text}</div>')


def panel(name: str | None = None):
    """A white panel. Use as a context manager: ``with kit.panel(): ...``."""
    return st.container(key=f"panel_{name or next(_counter)}")


# --------------------------------------------------------------------------- figures
@dataclass(frozen=True)
class Kpi:
    label: str
    value: str
    sub: str | None = None
    state: str | None = None   # within | watch | breach


def kpis(items: Sequence[Kpi]) -> None:
    cells = []
    for k in items:
        val = f"{dot(k.state)}{esc(k.value)}" if k.state else esc(k.value)
        sub = f'<div class="sub">{k.sub}</div>' if k.sub else ""
        cells.append(f'<div class="rk-kpi"><div class="lab">{esc(k.label)}</div><div class="val">{val}</div>{sub}</div>')
    render(f'<div class="rk-kpis">{"".join(cells)}</div>')


def dl(rows: Sequence[tuple[str, str]]) -> None:
    body = "".join(f"<dt>{esc(a)}</dt><dd>{b}</dd>" for a, b in rows)
    render(f'<dl class="rk-dl">{body}</dl>')


def checks(items: dict[str, bool]) -> None:
    spans = "".join(f'<span class="{"" if ok else "fail"}">{esc(k)}</span>' for k, ok in items.items())
    render(f'<div class="rk-checks">{spans}</div>')


def hero(*, label: str, var_d: float, var_pct: float, value: float, var_prev_d: float,
         rail_var: float, rail_es: float, rail_prev: float, limit_d: float,
         side: Sequence[tuple[str, str, str | None]], reading: str, rail_label: str = "") -> None:
    """Headline VaR plus the limit rail: 99% VaR, ES and yesterday's VaR placed against the limit."""
    use = rail_var / limit_d if limit_d else 0.0
    st_ = state_of_use(use)
    color = theme.ACCENT
    scale_max = max(limit_d * 1.3, rail_es * 1.12)

    def x(v: float) -> float:
        return max(0.0, min(100.0, v / scale_max * 100))

    change = var_d - var_prev_d
    # The VaR and limit tags sit side by side: the lower one ends at its mark, the higher one
    # starts at its mark, so they never overlap however close the two values are.
    left_end, right_start = "transform:translateX(calc(-100% + 1px))", "transform:translateX(-1px)"
    var_shift, lim_shift = (left_end, right_start) if rail_var <= limit_d else (right_start, left_end)
    side_html = "".join(
        f'<div><div class="lab">{esc(lab)}</div><div class="val">{val}'
        f'{f"<small>{esc(sm)}</small>" if sm else ""}</div></div>'
        for lab, val, sm in side
    )
    rail_caption = f'<span class="rk-rail-scale" style="left:0">{esc(rail_label)}</span>' if rail_label else ""
    render(f"""
<div class="rk-hero">
  <div class="rk-hero-top">
    <div>
      <div class="rk-hero-label">{esc(label)}</div>
      <div class="rk-hero-fig">{esc(theme.money(var_d))}</div>
      <div class="rk-hero-sub"><span class="fig">{esc(theme.pct(var_pct))}</span> of {esc(theme.money(value))}
        &nbsp;&nbsp;<span class="fig">{esc(theme.signed_money(change))}</span> since the previous day
        &nbsp;&nbsp;{status(st_, f"{use:.0%} of the 99% limit used")}</div>
    </div>
    <div class="rk-hero-side">{side_html}</div>
  </div>
  <div class="rk-rail">
    <div class="rk-rail-track"></div>
    <div class="rk-rail-es" style="left:{x(rail_var)}%;width:{max(0.0, x(rail_es) - x(rail_var))}%;background:{theme.ACCENT_SOFT}"></div>
    <div class="rk-rail-fill" style="width:{x(rail_var)}%;background:{color}"></div>
    <div class="rk-rail-prev" style="left:{x(rail_prev)}%" title="Previous day"></div>
    <div class="rk-rail-limit" style="left:{x(limit_d)}%"></div>
    <span class="rk-rail-tag top" style="left:{x(rail_var)}%;{var_shift}">99% VaR <b>{esc(theme.money(rail_var))}</b></span>
    <span class="rk-rail-tag top" style="left:{x(limit_d)}%;{lim_shift}">Limit <b>{esc(theme.money(limit_d))}</b></span>
    <span class="rk-rail-tag bottom" style="left:{x(rail_es)}%">99% ES <b>{esc(theme.money(rail_es))}</b></span>
    {rail_caption}
  </div>
  <div class="rk-hero-reading">{reading}</div>
</div>""")


# --------------------------------------------------------------------------- tables
@dataclass(frozen=True)
class Col:
    key: str
    label: str
    fmt: Callable[[object], str] | str | None = None    # format spec, callable, or None (str)
    num: bool = False
    kind: str = "text"            # text | bar | state | swatch | html
    bar_max: float | None = None
    marker_key: str | None = None  # for kind="bar": draws a tick at row[marker_key]
    dim: bool = False


def day(d: object) -> str:
    """Date formatter for table columns (handles missing dates)."""
    t = pd.Timestamp(d) if d is not None else pd.NaT
    return "–" if pd.isna(t) else f"{t:%d %b %Y}"


def _fmt(v: object, f) -> str:
    if v is None or (isinstance(v, float) and v != v) or v is pd.NaT:
        return "–"
    if callable(f):
        return f(v)
    if isinstance(f, str):
        return f.format(v)
    return str(v)


def table(df: pd.DataFrame, cols: Sequence[Col], highlight: Callable[[pd.Series], bool] | None = None,
          download: str | None = None, height: int | None = None, test_threshold: float = 0.05) -> None:
    head = "".join(f'<th class="{"num" if c.num else ""}">{esc(c.label)}</th>' for c in cols)
    rows = []
    for _, r in df.iterrows():
        tds = []
        for i, c in enumerate(cols):
            v = r.get(c.key)
            cls = []
            if c.num:
                cls.append("num")
            if i == 0:
                cls.append("key")
            if c.dim:
                cls.append("dim")
            if c.kind == "bar":
                mx = c.bar_max or float(df[c.key].abs().max() or 1)
                w = max(0.0, min(100.0, abs(float(v)) / mx * 100)) if v == v else 0
                mark = ""
                if c.marker_key is not None and r.get(c.marker_key) == r.get(c.marker_key):
                    m = max(0.0, min(100.0, abs(float(r[c.marker_key])) / mx * 100))
                    mark = f'<u style="left:{m}%"></u>'
                cell = f'<div class="rk-bar"><i style="width:{w}%"></i>{mark}</div>'
            elif c.kind == "state":
                cell = status(str(v[0]), str(v[1])) if isinstance(v, tuple) else esc(v)
            elif c.kind == "swatch":
                swatch = theme.ACCENT if str(v) == theme.focus() else "transparent"
                cell = f'<span class="rk-swatch" style="background:{swatch}"></span>{esc(v)}'
            elif c.kind == "test":
                cell = (status("within", "Pass") if v >= test_threshold else status("breach", "Reject")) if v == v else "–"
            elif c.kind == "html":
                cell = str(v)
            else:
                cell = esc(_fmt(v, c.fmt))
            tds.append(f'<td class="{" ".join(cls)}">{cell}</td>')
        tr_cls = "hl" if highlight is not None and highlight(r) else ""
        rows.append(f'<tr class="{tr_cls}">{"".join(tds)}</tr>')
    style = f' style="max-height:{height}px"' if height else ""
    scroll = " scroll" if height else ""
    render(f'<div class="rk-table-wrap{scroll}"{style}><table class="rk-table"><thead><tr>{head}</tr></thead>'
           f'<tbody>{"".join(rows)}</tbody></table></div>')
    if download:
        csv_download(df, download)


def csv_download(df: pd.DataFrame, name: str) -> None:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button("Download as CSV", buf.getvalue(), file_name=f"{name}.csv", mime="text/csv", key=f"dl_{name}")


# --------------------------------------------------------------------------- charts
_PLOT_CONFIG = {"displaylogo": False, "displayModeBar": "hover",
                "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
                "toImageButtonOptions": {"format": "png", "scale": 2}}


def plot(fig: go.Figure, height: int | None = None, key: str | None = None) -> None:
    """Draw a figure with the house settings (no title, white ground). Use inside a panel."""
    fig.update_layout(title_text="", paper_bgcolor=theme.SURFACE, plot_bgcolor=theme.SURFACE)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", key=key, theme=None, config=_PLOT_CONFIG)


def chart(fig: go.Figure, title: str | None = None, finding: str | None = None, note_text: str | None = None,
          height: int | None = None, key: str | None = None, aside: str | None = None) -> None:
    """A chart in a panel: the heading is HTML (statement-style), the figure has no title."""
    t = title if title is not None else (fig.layout.title.text or "")
    with panel(key):
        if t or finding:
            section(t, finding, aside)
        plot(fig, height, key)
        if note_text:
            note(note_text)
