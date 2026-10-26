"""Capture clean Streamlit dashboard screenshots for the presentation."""

from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "slides_assets" / "dashboard"
BASE_URL = "http://127.0.0.1:8501"

PAGES = {
    "data": ("/", "Data", "Same years, very different journeys", 0),
    "var": ("/var", "VaR & Expected Shortfall", "In plain words", 0),
    "backtesting": ("/backtesting", "Backtesting", "Actual P&L against VaR", 0),
    "stress": ("/stress", "Stress testing", "Worst scenario", 0),
    "risk_sources": ("/risk_sources", "Where the risk comes from", "Share of the money vs share of the ES", 0),
    "decisions": ("/decisions", "Decisions", "VaR before", 0),
}


def ready(driver: webdriver.Firefox, heading: str) -> bool:
    headings = driver.find_elements(By.TAG_NAME, "h1")
    return any(heading.lower() in element.text.lower() for element in headings)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    options = Options()
    options.add_argument("--headless")
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)

    driver = webdriver.Firefox(options=options)
    try:
        driver.set_window_size(1600, 1000)
        for name, (route, heading, ready_text, scroll_y) in PAGES.items():
            driver.get(f"{BASE_URL}{route}")
            WebDriverWait(driver, 90).until(lambda d, expected=heading: ready(d, expected))
            WebDriverWait(driver, 90).until(
                lambda d, expected=ready_text: expected.lower() in d.find_element(By.TAG_NAME, "body").text.lower()
            )
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, arguments[0]);", scroll_y)
            time.sleep(1)
            target = OUTPUT / f"dashboard_{name}.png"
            driver.save_screenshot(str(target))
            print(target)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
