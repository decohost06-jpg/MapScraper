import time
from urllib.parse import quote_plus
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class GoogleMapsBrowser:
    """Minimal Selenium wrapper to perform Google Maps searches.

    This is a starter implementation — selectors and flows may need
    updating as Google Maps front-end changes.
    """

    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        self.headless = headless
        self.user_agent = user_agent
        self.driver = None

    def start(self):
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        if self.user_agent:
            opts.add_argument(f"--user-agent={self.user_agent}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _wait_for_body(self, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def search(self, query: str, wait: int = 3) -> str:
        """Navigate to Google Maps search for the given query and return page HTML."""
        if not self.driver:
            self.start()

        url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        self.driver.get(url)
        try:
            self._wait_for_body(timeout=15)
        except Exception:
            pass

        # Give some time for dynamic results to render
        time.sleep(wait)
        return self.driver.page_source
