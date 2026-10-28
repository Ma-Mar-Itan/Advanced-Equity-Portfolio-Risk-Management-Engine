"""Capture individual Plotly charts from the live Streamlit dashboard."""

from __future__ import annotations

import re
import time
from pathlib import Path

from PIL import Image, ImageDraw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "slides_assets" / "dashboard_charts"
BASE_URL = "http://localhost:8501"
PAGES = {
    "data": "/",
    "cleaning": "/cleaning",
    "portfolio": "/portfolio",
    "volatility": "/volatility",
    "var": "/var",
    "backtesting": "/backtesting",
    "stress": "/stress",
    "risk_sources": "/risk-sources",
    "decisions": "/decisions",
}


def slug(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip()).strip("_").lower()
    return text[:70] or "chart"


def chart_label(element, index: int) -> str:
    parent = element.find_element(By.XPATH, "./ancestor::div[@data-testid='stVerticalBlock'][1]")
    headings = parent.find_elements(By.XPATH, ".//h2 | .//h3 | .//h4 | .//strong")
    for heading in reversed(headings):
        label = heading.text.strip()
        if label:
            return slug(label)
    return f"chart_{index + 1:02d}"


def build_contact_sheet(files: list[Path]) -> None:
    thumbs = []
    for file in files:
        image = Image.open(file).convert("RGB")
        image.thumbnail((520, 320))
        tile = Image.new("RGB", (540, 365), "white")
        tile.paste(image, ((540 - image.width) // 2, 28))
        ImageDraw.Draw(tile).text((12, 8), file.stem, fill="black")
        thumbs.append(tile)
    if not thumbs:
        return
    columns = 3
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 540, rows * 365), "#e5e5e5")
    for index, tile in enumerate(thumbs):
        sheet.paste(tile, ((index % columns) * 540, (index // columns) * 365))
    sheet.save(OUTPUT / "contact_sheet.jpg", quality=90)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    options = Options()
    options.add_argument("--headless")
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    driver = webdriver.Firefox(options=options)
    captured: list[Path] = []
    try:
        driver.set_window_size(1680, 1200)
        for page, route in PAGES.items():
            driver.get(f"{BASE_URL}{route}")
            WebDriverWait(driver, 120).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")) > 0
            )
            time.sleep(3)
            charts = driver.find_elements(By.CSS_SELECTOR, ".js-plotly-plot")
            for index, chart in enumerate(charts):
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", chart
                )
                time.sleep(0.4)
                label = chart_label(chart, index)
                target = OUTPUT / f"{page}_{index + 1:02d}_{label}.png"
                try:
                    chart.screenshot(str(target))
                except Exception as exc:  # Firefox can fail on unusually tall lazy charts.
                    print(f"Skipped {page} chart {index + 1}: {exc}")
                    continue
                captured.append(target)
                print(target)
    finally:
        driver.quit()
        if not captured:
            captured = sorted(OUTPUT.glob("*.png"))
        build_contact_sheet(captured)


if __name__ == "__main__":
    main()
