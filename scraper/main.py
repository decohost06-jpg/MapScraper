import sys
from pathlib import Path
import time
import random
import argparse
import pandas as pd

# Ensure the repository root is on PYTHONPATH when running scraper/main.py directly.
ROOT_DIR = Path(__file__).resolve().parent.parent
try:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from Config import (
        KEYWORDS,
        LOCATIONS,
        CATEGORIES,
        OUTPUT_PATH,
        MAX_RESULTS_PER_QUERY,
        HEADLESS,
        USER_AGENT,
        DELAY_RANGE,
        USE_PLAYWRIGHT,
    )
except ModuleNotFoundError:
    import importlib.util

    config_path = ROOT_DIR / "Config.py"
    spec = importlib.util.spec_from_file_location("Config", str(config_path))
    if spec is None or spec.loader is None:
        raise
    Config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Config)
    KEYWORDS = Config.KEYWORDS
    LOCATIONS = Config.LOCATIONS
    CATEGORIES = Config.CATEGORIES
    OUTPUT_PATH = Config.OUTPUT_PATH
    MAX_RESULTS_PER_QUERY = Config.MAX_RESULTS_PER_QUERY
    HEADLESS = Config.HEADLESS
    USER_AGENT = Config.USER_AGENT
    DELAY_RANGE = Config.DELAY_RANGE
    USE_PLAYWRIGHT = Config.USE_PLAYWRIGHT

from scraper.google_maps_browser import GoogleMapsBrowser
from scraper.parser import parse_places_from_html


def run_queries(use_playwright: bool = USE_PLAYWRIGHT):
    browser = None
    use_playwright_effective = use_playwright
    if use_playwright_effective:
        try:
            from scraper.playwright_browser import PlaywrightMaps
            browser = PlaywrightMaps(headless=HEADLESS, user_agent=USER_AGENT)
        except Exception as e:
            print(f"Playwright initialization failed: {e}. Falling back to Selenium.")
            use_playwright_effective = False

    if not use_playwright_effective:
        browser = GoogleMapsBrowser(headless=HEADLESS, user_agent=USER_AGENT)

    records = []

    try:
        for keyword in KEYWORDS:
            for location in LOCATIONS:
                for category in CATEGORIES:
                    query = " ".join(part for part in [keyword, category, "in", location] if part and part.strip())
                    if use_playwright_effective:
                        places = browser.search_places(query, max_results=MAX_RESULTS_PER_QUERY)
                    else:
                        try:
                            html = browser.search(query, wait=4)
                        except Exception as e:
                            raise
                        places = parse_places_from_html(html)

                    for p in places[:MAX_RESULTS_PER_QUERY]:
                        records.append({
                            "name": p.get("name"),
                            "phoneNumber": "; ".join(p.get("phone_candidates", [])),
                            "location": p.get("detail_location") or location,
                            "category": category,
                            "source_query": query,
                            "url": p.get("url"),
                        })

                    # polite delay between queries
                    time.sleep(random.uniform(*DELAY_RANGE))

    finally:
        try:
            browser.close()
        except Exception:
            pass

    df = pd.DataFrame(records)
    if df.empty:
        print("No results collected.")
    else:
        df.to_excel(OUTPUT_PATH, index=False)
        print(f"Saved {len(df)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Google Maps manual scraper")
    ap.add_argument("--use-playwright", action="store_true", help="Use Playwright instead of Selenium")
    ap.add_argument("--no-playwright", action="store_true", help="Use Selenium instead of Playwright")
    args = ap.parse_args()
    prefer_playwright = USE_PLAYWRIGHT
    if args.use_playwright:
        prefer_playwright = True
    if args.no_playwright:
        prefer_playwright = False
    run_queries(use_playwright=prefer_playwright)
