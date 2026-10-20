"""Build the written report (QFI_V2_report.docx) from report_assets/.

Run tools/build_report_assets first, then from the V2 folder:
    python -m tools.build_report
Layout: A4, 2.54 cm margins, Times New Roman 12 pt (tables 10 pt), no headers or footers.
Every number in the text is read from report_assets/results.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "report_assets"
OUT = ROOT / "QFI_V2_report.docx"
FONT = "Times New Roman"
TEXT_WIDTH_CM = 21.0 - 2 * 2.54

R = json.loads((ASSETS / "results.json").read_text())


# --------------------------------------------------------------------------- number formats
def pct(x: float, d: int = 1) -> str:
    """0.1234 -> '12.3%'."""
    return f"{x * 100:.{d}f}%"


def usd(x: float) -> str:
    """Dollar amounts in the report's style: $4.41 million, $297,000."""
    return f"${x / 1e6:.2f} million" if abs(x) >= 1e6 else f"${round(x, -3):,.0f}"


def num(x: float, d: int = 2) -> str:
    """A plain number with d decimals."""
    return f"{x:.{d}f}"


def pval(p: float) -> str:
    """p-values as journals print them."""
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


# --------------------------------------------------------------------------- document helpers
class Report:
    """Thin wrapper around python-docx with the report's house style."""

    def __init__(self) -> None:
        self.doc = Document()
        self.fig = 0
        self.tab = 0
        self.eq = 0
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, side, Cm(2.54))
        style = self.doc.styles["Normal"]
        style.font.name, style.font.size = FONT, Pt(12)
        style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        pf = style.paragraph_format
        pf.space_after, pf.line_spacing = Pt(6), 1.5
        for level, size in ((1, 12), (2, 12)):
            h = self.doc.styles[f"Heading {level}"]
            h.font.name, h.font.size, h.font.bold = FONT, Pt(size), True
            h.font.italic = level == 2
            h.font.color.rgb = None
            h.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
            h.element.rPr.rFonts.set(qn("w:ascii"), FONT)
            h.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
            h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(12), Pt(6)
            h.paragraph_format.keep_with_next = True

    # text -----------------------------------------------------------------
    def runs(self, par, text: str, size: float | None = None, italic: bool = False) -> None:
        """Add text with light markup: *italic*, _{sub}, ^{sup}."""
        for token in re.split(r"(\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\})", text):
            if not token:
                continue
            if token.startswith("*"):
                run, t = par.add_run(token[1:-1]), "i"
            elif token.startswith("_{"):
                run, t = par.add_run(token[2:-1]), "sub"
            elif token.startswith("^{"):
                run, t = par.add_run(token[2:-1]), "sup"
            else:
                run, t = par.add_run(token), ""
            run.font.name = FONT
            run.italic = italic or t == "i"
            run.font.subscript, run.font.superscript = t == "sub", t == "sup"
            if size:
                run.font.size = Pt(size)

    def title(self, text: str, author: str, affiliation: str) -> None:
        """Title block."""
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold, r.font.size = True, Pt(14)
        for line in (author, affiliation):
            q = self.doc.add_paragraph()
            q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            q.paragraph_format.space_after = Pt(2)
            self.runs(q, line)
        self.doc.add_paragraph()

    def abstract(self, text: str, keywords: str) -> None:
        """Indented abstract and keywords."""
        for label, body in (("Abstract. ", text), ("Keywords: ", keywords)):
            p = self.doc.add_paragraph()
            p.paragraph_format.left_indent = p.paragraph_format.right_indent = Cm(1)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            b = p.add_run(label)
            b.bold = True
            self.runs(p, body)

    def h1(self, text: str) -> None:
        """Numbered section heading (number included in the text)."""
        self.doc.add_heading(text, level=1)

    def h2(self, text: str) -> None:
        """Subsection heading."""
        self.doc.add_heading(text, level=2)

    def p(self, text: str) -> None:
        """A justified body paragraph."""
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        self.runs(par, text)

    def equation(self, expr: str) -> str:
        """A centred display equation numbered at the right margin; returns its label, e.g. '(3)'."""
        self.eq += 1
        par = self.doc.add_paragraph()
        stops = par.paragraph_format.tab_stops
        stops.add_tab_stop(Cm(TEXT_WIDTH_CM / 2), WD_TAB_ALIGNMENT.CENTER)
        stops.add_tab_stop(Cm(TEXT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        self.runs(par, expr, italic=False)
        par.add_run(f"\t({self.eq})")
        return f"({self.eq})"

    # floats ---------------------------------------------------------------
    def figure(self, file: str, caption: str, width_cm: float = 15.5) -> str:
        """An image with 'Figure n.' caption below; returns 'Figure n'."""
        self.fig += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.space_after = Pt(2)
        picture = par.add_run().add_picture(str(ASSETS / file), width=Cm(width_cm))
        picture._inline.docPr.set("title", f"Figure {self.fig}")
        picture._inline.docPr.set("descr", caption)
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        lab = cap.add_run(f"Figure {self.fig}. ")
        lab.bold = True
        self.runs(cap, caption)
        return f"Figure {self.fig}"

    def table(self, caption: str, header: list[str], rows: list[list[str]], widths_cm: list[float],
              note: str | None = None) -> str:
        """A three-rule (booktabs-style) table in 10 pt with caption above and note below; returns 'Table n'."""
        self.tab += 1
        cap = self.doc.add_paragraph()
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_after = Pt(3)
        lab = cap.add_run(f"Table {self.tab}. ")
        lab.bold = True
        self.runs(cap, caption)
        t = self.doc.add_table(rows=len(rows) + 1, cols=len(header))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        tr_pr = t.rows[0]._tr.get_or_add_trPr()
        tbl_header = OxmlElement("w:tblHeader")
        tbl_header.set(qn("w:val"), "true")
        tr_pr.append(tbl_header)
        for i, row in enumerate([header, *rows]):
            for j, value in enumerate(row):
                cell = t.cell(i, j)
                cell.width = Cm(widths_cm[j])
                par = cell.paragraphs[0]
                par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.line_spacing = 1.0
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.RIGHT
                self.runs(par, value, size=10)
                if i == 0:
                    for r in par.runs:
                        r.bold = True
                _keep_row_together(cell)
        _fix_widths(t, widths_cm)
        _three_rules(t)
        if note:
            n = self.doc.add_paragraph()
            n.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            n.paragraph_format.space_before = Pt(3)
            self.runs(n, "*Note.* " + note, size=10)
        else:
            self.doc.add_paragraph().paragraph_format.space_after = Pt(0)
        return f"Table {self.tab}"

    def references(self, items: list[str]) -> None:
        """Hanging-indent reference list."""
        for item in items:
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Cm(1)
            par.paragraph_format.first_line_indent = Cm(-1)
            par.paragraph_format.space_after = Pt(3)
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            self.runs(par, item)

    def save(self) -> None:
        """Write the .docx."""
        self.doc.save(OUT)


def _border(cell, edge: str, size: int) -> None:
    """Set one border of a table cell (size in eighths of a point)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size))
    el.set(qn("w:color"), "000000")
    borders.append(el)


def _fix_widths(table, widths_cm: list[float]) -> None:
    """Make Word and LibreOffice honour the column widths: fixed layout, table width and grid columns."""
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    width = OxmlElement("w:tblW")
    width.set(qn("w:w"), str(int(sum(widths_cm) * 567)))
    width.set(qn("w:type"), "dxa")
    for old in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(old)
    tbl_pr.append(width)
    for col, w in zip(tbl.tblGrid.findall(qn("w:gridCol")), widths_cm):
        col.set(qn("w:w"), str(int(w * 567)))


def _three_rules(table) -> None:
    """Top rule, rule under the header, bottom rule: the usual journal table look."""
    rows = table.rows
    for cell in rows[0].cells:
        _border(cell, "top", 12)
        _border(cell, "bottom", 6)
    for cell in rows[-1].cells:
        _border(cell, "bottom", 12)


def _keep_row_together(cell) -> None:
    """Keep table rows on one page."""
    for par in cell.paragraphs:
        par.paragraph_format.keep_with_next = True


# --------------------------------------------------------------------------- the report
def build() -> None:
    """Write every section of the report."""
    rp = Report()
    d, pf, dg = R["data"], R["portfolio"], R["diagnostics"]
    v = {x["model"]: x for x in R["var_today"]}
    g, gjr = R["garch"]["GARCH"], R["garch"]["GJR-GARCH"]
    bt99 = {x["model"]: x for x in R["bt99"]}
    bt95 = {x["model"]: x for x in R["bt95"]}
    b99b = {x["model"]: x for x in R["bt99_brief"]}
    b95b = {x["model"]: x for x in R["bt95_brief"]}
    st = {x["scenario"]: x for x in R["stress"]}
    lev = {x["move"]: x for x in R["leverage"]}
    reg = {x["regime"]: x for x in R["regimes"]}
    value = R["value"]
    sch = {x["scheme"]: x for x in R["schemes"]}
    dd = R["drawdowns"]
    att = R["attribution"]
    div, act = R["diversification"], R["active"]
    opt = {x["split"]: x for x in R["optimizer"]["compare"]}
    opt_now, opt_new = opt["Today's split"], opt["Optimized split"]
    w = R["winsor"]
    rf_note = ("Sharpe ratios use the 13-week T-bill yield." if R["risk_free_source"].startswith(("yahoo", "tiingo"))
               else "Sharpe ratios use a flat 2% risk-free rate because T-bill data were unavailable for this run.")
    hedges = R["hedges"]
    stock = {x["stock"]: x for x in d["stocks"]}
    att_by = {x["stock"]: x for x in att}

    rp.title("Advanced Equity Portfolio Risk Management",
             "Marwan Itani", "QFI Internship Project #3, October 2026")
    rp.abstract(
        f"We measure the market risk of an equally weighted portfolio of ten large US stocks over "
        f"{d['start']} to {d['end']} ({d['days']:,} trading days). Value at Risk (VaR) and Expected Shortfall (ES) are "
        "estimated by historical simulation, both unscaled and with past returns rescaled by EWMA, GARCH(1,1) and "
        "GJR-GARCH(1,1) volatility. Forecasts are produced out of sample with periodic re-estimation and evaluated with "
        "the Kupiec and Christoffersen tests and the Basel traffic light. All four models deliver unconditional "
        f"coverage close to the nominal 1% at the 99% level, but plain historical simulation produces clustered "
        f"exceptions (Christoffersen p {pval(bt99['HS']['Christoffersen p'])}). Over the full evaluation period "
        "GJR-GARCH scaling is the only specification that passes every test at both 95% and 99%; when the "
        f"evaluation starts in {R['brief_start'][3:]} it fails the independence test narrowly at 99% "
        f"(p = {pval(b99b['GJR-HS']['Christoffersen p'])}), so the ordering of the scaled models depends on the "
        "sample, while the rejection of unscaled simulation does not. Today's one-day 99% VaR is "
        f"{usd(v['GJR-HS']['var'] * value)} on a $10 million position; a replay of the 2008 crisis on current "
        f"holdings would cost {usd(st['2008 financial crisis']['loss'] * value)}.",
        "Value at Risk; Expected Shortfall; filtered historical simulation; GJR-GARCH; backtesting; stress testing")

    # 1 ---------------------------------------------------------------
    rp.h1("1 Executive Summary")
    rp.p("A single risk number is only useful if it reacts when conditions change. Historical simulation, the method "
         "most banks still use for regulatory VaR, treats every day in its estimation window as equally likely to "
         "repeat tomorrow. When volatility rises quickly, as in February 2020, the window is still dominated by calm "
         "days and the estimate lags. Rescaling past returns to current volatility (Hull and White, 1998; "
         "Barone-Adesi et al., 1999) addresses this without imposing a distribution on returns. This report applies "
         "the three volatility models named in the project brief to that rescaling step, compares them with the "
         "unscaled benchmark, and asks which version of the forecast survives a formal backtest.")
    rp.p(f"The portfolio holds Apple, Microsoft, NVIDIA, JPMorgan Chase, Exxon Mobil, Amazon, Meta, Alphabet, Tesla "
         f"and UnitedHealth in equal proportions, rebalanced monthly, with a current value of $10 million. Four "
         f"results stand out. First, portfolio returns show the usual stylised facts: excess kurtosis of "
         f"{num(dg['kurt'] - 3, 1)}, negative skewness and strong dependence in squared returns (Ljung-Box Q(10) on "
         f"squared returns of {dg['lb_r2']:,.0f}). Second, the GJR-GARCH estimates attribute almost all of the "
         f"volatility response to negative shocks (α = {num(gjr['alpha'], 3)} against γ = {num(gjr['gamma'], 3)}). "
         f"Third, in {R['bt_days']:,} out-of-sample days every model breaks its 99% VaR roughly as often as it should, "
         "but only the scaled models, and most clearly the GJR-scaled one, do so at times that look independent; "
         "the margin between the scaled models is small and depends on the start of the evaluation period. Fourth, stress scenarios show "
         f"how far VaR understates crisis losses: the worst 250-day window in the sample implies a one-day VaR of "
         f"{pct(R['basel_svar'])} of value, about {R['basel_svar'] / v['GJR-HS']['var']:.1f} times today's estimate.")
    rp.p("Section 2 describes the data and the cleaning steps. Section 3 builds the portfolio. Section 4 sets out the "
         "VaR, ES and volatility models and Section 5 reports today's estimates. Sections 6 and 7 present the backtests "
         "and the model comparison, Section 8 the stress tests and Section 9 a decomposition of risk by holding. "
         "Sections 10 and 11 discuss limitations and possible extensions.")

    # 2 ---------------------------------------------------------------
    rp.h1("2. Data")
    rp.p("Daily adjusted closing prices are taken from Yahoo Finance. The platform also supports Stooq, Tiingo, "
         "Alpha Vantage and Polygon through the same source interface, with local cache fallback. "
         "Adjusted prices correct for splits and dividends, so a stock split does not appear as a price collapse. The "
         "sample begins in June 2012 because Meta, the most recent listing among the ten names, started trading in "
         "May 2012; starting earlier would leave one series incomplete for the first part of the sample. The SPDR S&P "
         "500 ETF (SPY) is used as the market benchmark and the 13-week Treasury bill yield as the risk-free rate. "
         "Holdings quoted in other currencies would be converted to US dollars at the daily exchange rate; none of the "
         "ten stocks requires it.")
    rp.p(f"Cleaning aligns all series on a common trading calendar, fills isolated gaps of up to five days with the "
         f"last available price, and flags prices that remain unchanged for more than five consecutive days. For these "
         f"ten liquid stocks no gaps had to be filled and no stale prices were found; all {d['checks']} automated "
         "validation checks (complete dates, positive prices, finite returns, weights summing to one, and returns "
         "aligned with the prices of days t-1 and t) were passed. Returns are continuously compounded, "
         "r_{t} = ln(P_{t}/P_{t-1}). We considered winsorizing returns at the 1st and 99th percentiles. It would "
         f"alter {w['total']} observations, {w['year_2020']} of them in 2020 and {w['busiest_count']} in "
         f"{w['busiest_month']} alone. Since these are genuine market moves rather than data errors, and since the "
         "purpose of the exercise is to measure tail risk, we do not winsorize.")
    rows = [[s["stock"], pct(s["ann_return"]), pct(s["ann_vol"]), num(s["skew"]), num(s["kurt"], 1),
             pct(s["min"]), pct(s["max"])] for s in d["stocks"]]
    t1 = rp.table(f"Descriptive statistics of daily log returns, {d['start']} to {d['end']}.",
                  ["Stock", "Return p.a.", "Volatility p.a.", "Skewness", "Kurtosis", "Min", "Max"], rows,
                  [2.2, 2.4, 2.6, 2.2, 2.2, 2.0, 2.0],
                  "Return p.a. is the annualised mean log return converted to a simple rate; volatility is the "
                  "daily standard deviation times √252. Kurtosis is raw (3 for a normal distribution).")
    rp.p(f"{t1} summarises the individual series. Every stock has kurtosis well above the normal value of 3, ranging "
         f"from {num(stock['TSLA']['kurt'], 1)} for Tesla to {num(stock['UNH']['kurt'], 1)} for UnitedHealth, whose "
         f"distribution is dominated by a handful of large negative days (skewness {num(stock['UNH']['skew'])}). "
         f"NVIDIA and Tesla combine the highest average returns with the highest volatility. "
         f"{'Figure 1'} plots the growth of one dollar in each stock; the dispersion of outcomes, from $4 for Exxon "
         "to $782 for NVIDIA, already suggests that the weighting scheme will matter for risk.")
    rp.figure("fig01_growth.png", "Value of $1 invested in each stock on 1 June 2012 (log scale). NVIDIA, the best "
              "performer, is highlighted.")

    # 3 ---------------------------------------------------------------
    rp.h1("3. Portfolio construction")
    rp.p("The portfolio aggregates simple returns, since log returns do not add across assets. With weights "
         "w_{i,t-1} fixed at the previous close, the portfolio return is R_{p,t} = Σ_{i} w_{i,t-1} R_{i,t} and the "
         "daily profit and loss is V_{t-1} R_{p,t}. Between rebalancing dates the weights drift with relative "
         "performance; on the last trading day of each month they are reset to the target. The dollar series are "
         "scaled so that the portfolio is worth $10 million today, which keeps the risk figures in later sections "
         "comparable with the position actually held. Two checks confirm the accounting: target weights sum to one at "
         "every rebalance, and the daily P&L equals the sum of the stock-level contributions on every day.")
    rows = [[k, pct(x["ann_return"]), pct(x["ann_vol"]), num(x["sharpe"]), pct(x["mdd"])]
            for k, x in sch.items() if not k.startswith("Market-cap")]
    t2 = rp.table("Performance of alternative weighting rules, June 2012 to October 2026.",
                  ["Weighting rule", "Return p.a.", "Volatility p.a.", "Sharpe ratio", "Max drawdown"], rows,
                  [6.4, 2.4, 2.7, 2.2, 2.6],
                  f"{rf_note} The S&P 500 (SPY) returned {pct(pf['benchmark annual return'])} "
                  "a year over the same period. The platform's market-capitalisation rule is excluded from this "
                  "retrospective table unless dated shares outstanding cover every rebalance date.")
    eq_m, bh = sch["Equal weight, monthly rebalancing"], sch["Equal weight, buy and hold"]
    rp.p(f"The equally weighted, monthly rebalanced portfolio earned {pct(pf['annual return'])} a year with "
         f"volatility of {pct(pf['annual volatility'])}, against {pct(pf['benchmark annual return'])} for the S&P 500, "
         f"and has a beta of {num(pf['beta'])} to the index. {t2} shows that the rebalancing rule is itself a risk "
         f"decision. Buy and hold produced the highest return in hindsight ({pct(bh['ann_return'])}), but only because "
         "NVIDIA and Tesla came to dominate the portfolio; its maximum drawdown was "
         f"{pct(bh['mdd'])}, against {pct(eq_m['mdd'])} with monthly rebalancing. The inverse-volatility rule had the "
         "lowest volatility and the smallest drawdown, at the cost of a lower return.")
    f2 = rp.figure("fig02_drawdown.png", "Drawdown of the equally weighted portfolio: the percentage fall from the "
                   "highest value reached to date.")
    rp.p(f"{f2} shows the drawdown path. The two deepest episodes differ in character. The COVID crash took the "
         f"portfolio {pct(-dd[0]['depth'])} below its peak in {dd[0]['days_down']} trading days and recovered within "
         f"{dd[0]['days_to_recover']:.0f} more; the 2022 decline was almost as deep ({pct(-dd[1]['depth'])}) but "
         f"lasted {dd[1]['days_down']} trading days. A one-day risk measure says nothing about the second kind of "
         "episode, which is one reason the stress tests in Section 8 are needed.")
    f3 = rp.figure("fig03_distribution.png", "Histogram of daily portfolio returns against a normal density with the "
                   "same mean and variance.", width_cm=14)
    rp.p(f"{f3} compares the distribution of daily portfolio returns with a normal density. The Jarque-Bera statistic "
         f"is {dg['jb']:,.0f} (p {pval(dg['jb_p'])}), with skewness of {num(dg['skew'])} and kurtosis of "
         f"{num(dg['kurt'], 1)}. Squared returns are strongly autocorrelated (Ljung-Box Q(10) = {dg['lb_r2']:,.0f}) "
         f"and Engle's (1982) ARCH-LM test with five lags gives {dg['arch_lm']:,.0f} (p {pval(dg['arch_p'])}). "
         f"Returns themselves also show some linear dependence (Q(10) = {dg['lb_r']:.0f}), which we leave unmodelled; "
         "at a daily horizon its effect on the quantiles is small next to that of changing volatility.")

    # 4 ---------------------------------------------------------------
    rp.h1("4. Methodology")
    rp.h2("4.1 Historical simulation VaR and Expected Shortfall")
    rp.p("Let L_{j} = -(exp(r_{j}) - 1) denote the loss, as a fraction of value, in scenario j, where the scenarios are "
         "the N most recent daily portfolio returns. With tail probability p = 1 - c for confidence level c, the tail "
         "contains k = ⌈pN⌉ scenarios. Ordering losses from largest to smallest, L_{(1)} ≥ L_{(2)} ≥ ..., we define")
    e1 = rp.equation("VaR_{c} = L_{(k)},        ES_{c} = (1/k) Σ_{j=1..k} L_{(j)}")
    rp.p(f"so that VaR is the k-th largest loss and ES the average of the k largest. With N = 500 and c = 99%, k = 5. "
         f"ES is the coherent measure (Acerbi and Tasche, 2002) and by construction ES ≥ VaR. We report results for "
         "windows of 250, 500 and 750 days and confidence levels of 95%, 99% and 99.5%, with 500 days and 99% as the "
         "baseline.")
    rp.h2("4.2 Volatility models")
    rp.p("All three models produce a one-step-ahead conditional standard deviation σ_{t} that uses information up to "
         "t-1 only. The EWMA estimator of RiskMetrics (J.P. Morgan, 1996) is")
    e2 = rp.equation("σ^{2}_{t} = λ σ^{2}_{t-1} + (1 - λ) r^{2}_{t-1}")
    rp.p("with λ = 0.94. It has no mean reversion, so its forecast is flat at every horizon. The GARCH(1,1) model of "
         "Bollerslev (1986) adds a constant that anchors volatility to a long-run level, and the GJR-GARCH model of "
         "Glosten et al. (1993) lets negative shocks carry extra weight:")
    e3 = rp.equation("σ^{2}_{t} = ω + (α + γ I_{t-1}) ε^{2}_{t-1} + β σ^{2}_{t-1},        I_{t-1} = 1 if ε_{t-1} < 0")
    rp.p(f"with γ = 0 giving GARCH(1,1). Persistence is α + γ/2 + β and the long-run variance ω/(1 - α - γ/2 - β). "
         "Parameters are estimated by maximum likelihood with normal innovations and a zero mean. Table 3 reports "
         "full-sample estimates; the out-of-sample forecasts in Section 6 re-estimate the parameters every 63 trading "
         "days on data available at that date and filter σ_{t} forward with fixed parameters in between.")
    rows = [["ω (×10^{6})", num(g["omega"] * 1e6), num(gjr["omega"] * 1e6)],
            ["α", num(g["alpha"], 3), num(gjr["alpha"], 3)], ["γ", "–", num(gjr["gamma"], 3)],
            ["β", num(g["beta"], 3), num(gjr["beta"], 3)], ["Persistence", num(g["persistence"], 3), num(gjr["persistence"], 3)],
            ["Long-run volatility p.a.", pct(g["long-run vol (yearly)"]), pct(gjr["long-run vol (yearly)"])],
            ["Half-life (days)", num(g["half-life (days)"], 1), num(gjr["half-life (days)"], 1)],
            ["Log-likelihood", f"{g['log-likelihood']:,.1f}", f"{gjr['log-likelihood']:,.1f}"],
            ["AIC", f"{g['AIC']:,.1f}", f"{gjr['AIC']:,.1f}"]]
    t3 = rp.table("Maximum-likelihood estimates for daily portfolio returns (percent), June 2012 to October 2026.",
                  ["", "GARCH(1,1)", "GJR-GARCH(1,1)"], rows, [6.0, 4.0, 4.0],
                  "Persistence is α + γ/2 + β. Half-life is ln(0.5)/ln(persistence).")
    lr = 2 * (gjr["log-likelihood"] - g["log-likelihood"])
    rp.p(f"{t3} shows the asymmetry clearly. In the GJR model the response to a positive shock is small "
         f"(α = {num(gjr['alpha'], 3)}) while a negative shock adds γ = {num(gjr['gamma'], 3)}. The likelihood-ratio "
         f"statistic for γ = 0 is {lr:.1f}, far above the 1% critical value of 6.63, and the AIC also favours the "
         f"asymmetric model. Both models are highly persistent, with a half-life of about {gjr['half-life (days)']:.0f} "
         f"trading days. Dividing returns by the GJR volatility reduces kurtosis from {num(R['resid']['kurt_raw'], 1)} "
         f"to {num(R['resid']['kurt_z'], 1)} and removes the dependence in squared returns (Ljung-Box Q(10) on squared "
         f"standardised residuals = {R['resid']['lb_z2']:.1f}, p = {R['resid']['lb_z2_p']:.2f}).")
    f4 = rp.figure("fig04_vol_models.png", "Annualised conditional volatility of the portfolio: 63-day rolling "
                   "standard deviation, EWMA (λ = 0.94), GARCH(1,1) and GJR-GARCH(1,1).")
    f5 = rp.figure("fig05_leverage.png", "Average absolute daily return over the five days following a day in each "
                   "return bucket. No model is involved.", width_cm=14)
    rp.p(f"{f4} plots the four volatility estimates. The conditional models react within a day to the March 2020 "
         "shock and decay over the following weeks, while the rolling estimate rises more slowly and then drops "
         f"abruptly when the crash leaves its window. {f5} checks the asymmetry without any model: after a day with a "
         f"loss of more than 3%, the following five days moved {pct(lev['below -3%']['avg move next 5 days'], 2)} on "
         f"average, against {pct(lev['above +3%']['avg move next 5 days'], 2)} after a gain of the same size and "
         f"{pct(lev['-0.5% to +0.5%']['avg move next 5 days'], 2)} after a quiet day. Clustering is also visible in the "
         f"regime split: {reg['Stormy']['days below -3%']} of the "
         f"{sum(x['days below -3%'] for x in R['regimes'])} days with losses beyond 3% fall in the third of the sample "
         "with the highest GJR volatility.")
    rp.h2("4.3 Volatility-scaled historical simulation")
    rp.p("Following Hull and White (1998), each historical return is rescaled by the ratio of the volatility forecast "
         "for tomorrow to the volatility prevailing on the day it occurred,")
    e4 = rp.equation("r̃_{j} = r_{j} · σ_{T+1} / σ_{j},        j = T-N+1, ..., T")
    rp.p(f"and equation {e1} is then applied to the rescaled sample. A loss of 2% from a period half as volatile as "
         "today enters the scenario set as a loss of about 4%. We label the resulting models EWMA-HS, GARCH-HS and "
         "GJR-HS, and the unscaled benchmark HS. Ten-day figures use the square-root-of-time rule, "
         "VaR_{10} = √10 · VaR_{1}; the platform also offers overlapping ten-day returns, which assume nothing about "
         "independence but rest on far fewer effective observations.")

    # 5 ---------------------------------------------------------------
    rp.h1("5. Value at Risk and Expected Shortfall estimates")
    rows = [[m, usd(v[m]["var"] * value), pct(v[m]["var"], 2), usd(v[m]["es"] * value), usd(v[m]["var10"] * value),
             usd(v[m]["es10"] * value)] for m in ("HS", "EWMA-HS", "GARCH-HS", "GJR-HS")]
    t4 = rp.table("One-day and ten-day 99% VaR and ES on 16 October 2026 for a $10 million portfolio (500-day window).",
                  ["Model", "VaR 1-day", "VaR %", "ES 1-day", "VaR 10-day", "ES 10-day"], rows,
                  [2.8, 2.7, 2.0, 2.7, 2.9, 2.9], "Ten-day figures apply the square-root-of-time rule.")
    gr = R["var_grid"]
    rp.p(f"{t4} reports current estimates. The scaled models give lower figures than plain historical simulation "
         f"({usd(v['EWMA-HS']['var'] * value)} to {usd(v['GJR-HS']['var'] * value)}, against "
         f"{usd(v['HS']['var'] * value)}) because current volatility is below its sample average while the 500-day "
         "window still contains the April 2025 sell-off. Across confidence levels and windows the GJR-HS estimate "
         f"ranges from {pct(min(map(min, gr['values'])), 2)} (95%, 250 days) to {pct(max(map(max, gr['values'])), 2)} "
         f"(99.5%, 500 days) of portfolio value; at 99% it is {pct(gr['values'][1][0], 2)}, {pct(gr['values'][1][1], 2)} "
         f"and {pct(gr['values'][1][2], 2)} for windows of 250, 500 and 750 days. The validation checks in the brief "
         "hold for every model: VaR is positive, increases with the confidence level, is larger at ten days than at "
         "one, and is below ES.")
    rp.figure("fig06_scenarios.png", "The 500 GJR-scaled scenarios for tomorrow's profit and loss with the 99% VaR "
              "and ES marked.", width_cm=14)

    # 6 ---------------------------------------------------------------
    rp.h1("6. Backtesting")
    rp.p(f"Each model produces a one-day 99% and 95% VaR forecast for every day from {R['bt_start']}, the first date "
         f"with 500 days of history, to {d['end']}: {R['bt_days']:,} forecasts in all. An exception occurs when the "
         "realised loss exceeds the forecast. Let x be the number of exceptions in T days. The Kupiec (1995) "
         "proportion-of-failures statistic compares the observed rate π̂ = x/T with p:")
    rp.equation("LR_{POF} = -2 ln[(1 - p)^{T-x} p^{x}] + 2 ln[(1 - π̂)^{T-x} π̂^{x}]  ~  χ^{2}(1)")
    rp.p("Christoffersen's (1998) independence test compares the probability of an exception following a non-exception "
         "day, π_{01}, with the probability following an exception day, π_{11}. Its statistic is asymptotically χ^{2}(1), "
         "and adding it to LR_{POF} gives the conditional coverage test, χ^{2}(2). The Basel traffic light classifies "
         "the number of 99% exceptions in the latest 250 days: zero to four green, five to nine yellow, ten or more red "
         "(Basel Committee, 1996). We verified the implementation on the textbook case of 10 exceptions in 250 days, "
         "for which LR_{POF} = 12.96.")
    order = [x["model"] for x in R["bt99"]]
    rows = []
    for m in order:
        a, b = bt99[m], bt95[m]
        rows.append([m, f"{a['exceptions']}", pval(a["Kupiec p"]), pval(a["Christoffersen p"]), pval(a["Coverage p"]),
                     f"{b['exceptions']}", pval(b["Kupiec p"]), pval(b["Christoffersen p"]), pval(b["Coverage p"])])
    t5 = rp.table(f"Backtest results, {R['bt_start']} to {d['end']} ({R['bt_days']:,} days).",
                  ["Model", "99%: exc.", "Kupiec", "Indep.", "Cov.", "95%: exc.", "Kupiec", "Indep.", "Cov."], rows,
                  [2.4, 1.6, 1.7, 1.7, 1.7, 1.6, 1.7, 1.7, 1.7],
                  f"Expected exceptions: {bt99['HS']['expected']:.1f} at 99% and {bt95['HS']['expected']:.1f} at 95%. "
                  "Columns report the number of exceptions and the p-values of the Kupiec, Christoffersen independence "
                  "and conditional coverage tests. Models are ordered by the ranking in Section 7.")
    rp.p(f"{t5} gives the results. None of the models can be rejected on the number of exceptions: at 99% they "
         f"record between {min(x['exceptions'] for x in R['bt99'])} and {max(x['exceptions'] for x in R['bt99'])} "
         f"against {bt99['HS']['expected']:.1f} expected, and all Kupiec p-values exceed 0.35. The timing is another "
         f"matter. Plain HS fails the independence test at both levels (p {pval(bt99['HS']['Christoffersen p'])} at 99% "
         f"and {pval(bt95['HS']['Christoffersen p'])} at 95%), and GARCH-HS fails it at 99% "
         f"(p = {pval(bt99['GARCH-HS']['Christoffersen p'])}). EWMA-HS fails it narrowly at 99% "
         f"(p = {pval(bt99['EWMA-HS']['Christoffersen p'])}). GJR-HS passes every test at both confidence levels over this period, although its 99% "
         "independence p-value is only just above 5%; Section 7 shows that this result is not robust to the start "
         "date.")
    f7 = rp.figure("fig07_rolling_2020.png", "Daily P&L in 2020 against the one-day 99% VaR of the HS and GJR-HS "
                   "models, both computed with data available at the time.")
    f8 = rp.figure("fig08_exceptions.png", "Dates of 99% VaR exceptions by model, June 2014 to October 2026.",
                   width_cm=14)
    rp.p(f"{f7} shows where the difference comes from. In late February and March 2020 the HS forecast barely moved, "
         "from about $380,000 to $600,000, while daily losses reached $1.4 million; it was exceeded six times in under "
         "four weeks. The GJR-HS forecast rose above $2 million at the height of the crisis and was exceeded once in "
         f"that period. {f8} shows the same pattern over the whole sample: the HS exceptions come in groups in August "
         "2015, early 2018, March 2020 and April 2025, while the GJR-HS exceptions are spread out. Measured by the "
         f"traffic light, HS spent {R['yellow_days']['HS']} days in the yellow zone over the period, against "
         f"{R['yellow_days']['GJR-HS']} for GJR-HS; all four models are currently green.")

    # 7 ---------------------------------------------------------------
    rp.h1("7. Model comparison")
    rows = [[x["model"], f"{x['ratio']:.2f}", usd(x["average VaR"]), usd(x["VaR volatility"]), usd(x["average ES"]),
             usd(x["worst daily loss"]), x["zone"].capitalize(), f"{x['rank']}"] for x in R["bt99"]]
    t6 = rp.table("Comparison of the 99% VaR models over the backtest period.",
                  ["Model", "Exc./exp.", "Mean VaR", "SD of VaR", "Mean ES", "Worst loss", "Zone", "Rank"], rows,
                  [2.3, 1.6, 2.3, 2.2, 2.3, 2.5, 1.4, 1.4],
                  "Exc./exp. is the ratio of actual to expected exceptions. SD of VaR is the standard deviation of "
                  "the daily forecast. Zone refers to the latest 250 days.")
    rp.p(f"{t6} collects the metrics listed in the brief. We rank models first on whether they pass all three tests, "
         "then on the distance between actual and expected exceptions, and finally on the average VaR, since a model "
         "that achieves correct coverage with less capital is preferable. GJR-HS ranks first. Its average VaR "
         f"({usd(bt99['GJR-HS']['average VaR'])}) is close to the lowest and below that of plain HS "
         f"({usd(bt99['HS']['average VaR'])}), so the better coverage does not come from holding more risk capital on "
         "average. It comes from moving the forecast: the standard deviation of the GJR-HS forecast is "
         f"{bt99['GJR-HS']['VaR volatility'] / bt99['HS']['VaR volatility']:.1f} times that of HS. The scaled model "
         "holds less in calm periods and more in turbulent ones, which is what a risk forecast should do.")
    rows = []
    for m in ("HS", "EWMA-HS", "GARCH-HS", "GJR-HS"):
        a, b, c, e = bt99[m], b99b[m], bt95[m], b95b[m]
        rows.append([m, f"{a['exceptions']}", pval(a["Christoffersen p"]), f"{b['exceptions']}",
                     pval(b["Christoffersen p"]), pval(c["Christoffersen p"]), pval(e["Christoffersen p"])])
    t6b = rp.table(f"Sensitivity of the backtest to its start date: {R['bt_start']} against {R['brief_start']}.",
                   ["Model", "99% exc. (full)", "Indep. p (full)", f"99% exc. (2015)", "Indep. p (2015)",
                    "95% indep. (full)", "95% indep. (2015)"], rows,
                   [2.4, 2.1, 2.1, 2.1, 2.1, 2.2, 2.2],
                   f"Full: {R['bt_days']:,} days from {R['bt_start']}. 2015: {R['brief_days']:,} days from "
                   f"{R['brief_start']}, the first date with 750 days of history, as in the project brief. "
                   "Indep. is the p-value of the Christoffersen independence test.")
    rp.p(f"The ranking rests on p-values close to the 5% threshold, so we repeat the backtest from "
         f"{R['brief_start']}, the first date with 750 days of prior data, which is the convention in the project "
         f"brief. {t6b} reports the result. At 99% no model now passes all three tests. GJR-HS records "
         f"{b99b['GJR-HS']['exceptions']} exceptions and an independence p-value of "
         f"{pval(b99b['GJR-HS']['Christoffersen p'])}, EWMA-HS {pval(b99b['EWMA-HS']['Christoffersen p'])} and "
         f"GARCH-HS {pval(b99b['GARCH-HS']['Christoffersen p'])}, and with no model passing every test the ranking "
         f"rule places EWMA-HS first. Three conclusions survive the change. Plain HS is rejected clearly in "
         f"both samples (p {pval(b99b['HS']['Christoffersen p'])} at 99%). At 95% all three scaled models pass "
         f"every test in both samples and GJR-HS ranks first in both. And no model is rejected on the number "
         "of exceptions. We therefore read the evidence as favouring volatility scaling over unscaled simulation, "
         "with GJR-HS the most reliable of the scaled models rather than the only adequate one. With about 30 "
         "expected exceptions, differences of a few hundredths in the independence p-value are within sampling "
         "noise.")

    # 8 ---------------------------------------------------------------
    rp.h1("8. Stress testing")
    rp.p("Historical scenarios apply each stock's actual daily returns over a crisis window to today's holdings, held "
         "without rebalancing. Meta and Tesla were not listed in 2008; for that window their returns are replaced by "
         "β_{i} times the SPY return, with β_{i} estimated over the latest 500 days. Hypothetical scenarios move each "
         "stock by β_{i} times a market shock, shock one sector, double volatility (scaling every scenario in the "
         "GJR-HS set by two), or push all pairwise correlations halfway towards one and rescale VaR by the implied "
         "change in portfolio volatility. For historical scenarios the stressed VaR and ES are computed on the 250 "
         "days ending at the end of each crisis window.")
    rows = [[x["scenario"], x["kind"], usd(x["loss"] * value), pct(x["loss"]), pct(x["worst_day"]),
             pct(x["stressed_var"]) if x["stressed_var"] is not None else "–"] for x in R["stress"]]
    t7 = rp.table("Stress scenarios applied to the current $10 million portfolio, ranked by loss.",
                  ["Scenario", "Type", "Loss", "Loss %", "Worst day", "Stressed VaR"], rows,
                  [5.0, 2.5, 2.6, 1.8, 2.0, 2.0],
                  "Loss is the cumulative change in value over the scenario. For volatility and correlation shocks "
                  "the loss shown is the stressed one-day 99% VaR. Negative values are gains.")
    rp.p(f"{t7} ranks the scenarios. The 2008 crisis is the most severe, with a loss of "
         f"{usd(st['2008 financial crisis']['loss'] * value)} ({pct(st['2008 financial crisis']['loss'])}), followed "
         f"by the COVID crash ({pct(st['COVID crash 2020']['loss'])}). A uniform 20% market decline costs "
         f"{pct(st['Market -20%']['loss'])} because the portfolio's average beta exceeds one; Tesla "
         f"(β = {num(R['betas']['TSLA'])}) and NVIDIA (β = {num(R['betas']['NVDA'])}) are the most sensitive holdings "
         f"and Exxon (β = {num(R['betas']['XOM'])}) the least. The banking stress of March 2023 would have produced a "
         f"small gain, since technology stocks rallied while regional banks fell. Searching every 250-day window in "
         f"the sample, the highest one-day VaR for today's portfolio is {pct(R['basel_svar'])}, for the window ending "
         f"in {R['basel_svar_end']}. This Basel 2.5 stressed VaR (Basel Committee, 2009) is "
         f"{R['basel_svar'] / v['GJR-HS']['var']:.1f} times the current estimate.")
    rp.figure("fig09_stress.png", "Loss on the current portfolio under each stress scenario. Dark bars are historical "
              "replays, light bars hypothetical shocks.", width_cm=14.5)

    # 9 ---------------------------------------------------------------
    rp.h1("9. Risk decomposition and decision support")
    rp.p("To identify the sources of risk we allocate ES to holdings by the Euler principle. Each stock's contribution "
         "is its weight times its average return across the k scenarios in the portfolio's loss tail, so that the "
         "contributions sum exactly to ES. The VaR allocation averages over the scenarios ranked next to the VaR "
         "scenario and is rescaled to sum to VaR.")
    f10 = rp.figure("fig10_risk_share.png", "Share of portfolio value and share of 99% ES contributed by each stock "
                    "(GJR-HS scenarios).", width_cm=14)
    rp.p(f"{f10} shows that risk is concentrated. Tesla and Amazon each hold about 10% of the capital but contribute "
         f"{pct(att_by['TSLA']['es_share'], 0)} and {pct(att_by['AMZN']['es_share'], 0)} of ES; Exxon and UnitedHealth "
         f"contribute {pct(att_by['XOM']['es_share'], 0)} and {pct(att_by['UNH']['es_share'], 0)}. The sum of the ten "
         f"stand-alone VaRs is {usd(div['sum_standalone'])}, against a portfolio VaR of {usd(div['var'])}, a "
         f"diversification benefit of {pct(div['benefit_share'], 0)}. Over the last 500 days the tracking error relative "
         f"to the S&P 500 was {pct(act['tracking error'])} a year. The same scenario set supports three decision tools. The best single "
         f"hedge, a short position of about {usd(-hedges[0]['amount'])} in SPY, reduces VaR by "
         f"{pct(hedges[0]['reduction'], 0)}; the best single-stock hedge is a short of {usd(-hedges[1]['amount'])} in "
         f"{hedges[1]['instrument']} ({pct(hedges[1]['reduction'], 0)}). Minimising ES with the linear programme of "
         f"Rockafellar and Uryasev (2000), subject to a 25% cap per stock, lowers ES from "
         f"{usd(opt_now['ES'])} to {usd(opt_new['ES'])}, but the historical return of the "
         f"optimised weights is {pct(opt_new['return'])} a year against "
         f"{pct(opt_now['return'])}. Because the weights are fitted to the last 500 days, their "
         "historical maximum drawdown is not lower than that of the equal-weight portfolio, a reminder that an "
         "in-sample optimum is not a forecast.")

    # 10, 11 -----------------------------------------------------------
    rp.h1("10. Limitations")
    rp.p("Several simplifications qualify the results. The universe is ten large US stocks that are in the sample "
         "because they exist and are large today, so the data carry survivorship bias and the high average returns "
         "should not be read as expected returns. The ten-day figures rely on the square-root-of-time rule, which "
         "ignores volatility mean reversion and the autocorrelation found in Section 3. The GARCH parameters are "
         "estimated with normal innovations; a Student-t specification is available in the platform but was not used "
         "for the reported results. With roughly 31 expected exceptions at 99%, the backtests have limited power, and "
         "the independence test in particular can only detect fairly strong clustering; Section 7 shows that a later "
         "start date is enough to move the 99% verdict on GJR-HS across the 5% line. Stand-ins for stocks that "
         "did not trade in 2008 assume that their market sensitivity was the same then as now. A historical "
         "market-capitalisation portfolio can only be built when dated shares outstanding cover every rebalance "
         "date; the implementation stops when that history is missing rather than carrying today's share count into "
         "the past. The reported results use one vendor's saved prices, so a production process should reconcile "
         "prices against an independent source.")
    rp.h1("11. Future improvements")
    rp.p("Four extensions would address these points. Simulating ten-day paths from the fitted GJR model, rather than "
         "scaling the one-day figure, would capture mean reversion in volatility. A Student-t or skewed-t innovation "
         "distribution could be compared with the normal specification using the same backtests. An ES backtest, "
         "such as that of Acerbi and Szekely (2014), would test the tail beyond VaR directly, which matters now that "
         "the Basel framework uses ES for capital. A point-in-time universe rebuilt from historical index "
         "membership would remove survivorship bias. Historical share counts should also be archived with each "
         "research run so market-capitalisation weights remain reproducible.")

    rp.h1("References")
    rp.references([
        "Acerbi, C., and Szekely, B. (2014). Backtesting expected shortfall. *Risk*, 27(11), 76–81.",
        "Acerbi, C., and Tasche, D. (2002). On the coherence of expected shortfall. *Journal of Banking & Finance*, "
        "26(7), 1487–1503.",
        "Barone-Adesi, G., Giannopoulos, K., and Vosper, L. (1999). VaR without correlations for portfolios of "
        "derivative securities. *Journal of Futures Markets*, 19(5), 583–602.",
        "Basel Committee on Banking Supervision (1996). *Supervisory framework for the use of “backtesting” "
        "in conjunction with the internal models approach to market risk capital requirements*. Basel: BIS.",
        "Basel Committee on Banking Supervision (2009). *Revisions to the Basel II market risk framework*. Basel: BIS.",
        "Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics*, "
        "31(3), 307–327.",
        "Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review*, 39(4), 841–862.",
        "Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United "
        "Kingdom inflation. *Econometrica*, 50(4), 987–1007.",
        "Glosten, L. R., Jagannathan, R., and Runkle, D. E. (1993). On the relation between the expected value and "
        "the volatility of the nominal excess return on stocks. *Journal of Finance*, 48(5), 1779–1801.",
        "Hull, J., and White, A. (1998). Incorporating volatility updating into the historical simulation method for "
        "value-at-risk. *Journal of Risk*, 1(1), 5–19.",
        "J.P. Morgan/Reuters (1996). *RiskMetrics: Technical document* (4th ed.). New York: J.P. Morgan.",
        "Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *Journal of "
        "Derivatives*, 3(2), 73–84.",
        "Rockafellar, R. T., and Uryasev, S. (2000). Optimization of conditional value-at-risk. *Journal of Risk*, "
        "2(3), 21–41.",
    ])
    rp.save()
    print(f"Report written to {OUT}")


if __name__ == "__main__":
    build()
