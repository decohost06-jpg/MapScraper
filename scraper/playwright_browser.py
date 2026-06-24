from urllib.parse import quote_plus
from typing import Any, Dict, List, Optional


class PlaywrightMaps:
    """Playwright-based Google Maps search helper."""

    def __init__(self, headless: bool = True, user_agent: Optional[str] = None):
        self.headless = headless
        self.user_agent = user_agent
        self._play = None
        self._browser = None
        self._context = None
        self.page = None

    def start(self):
        if self._play:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError("Playwright is not available. Install playwright and run 'playwright install'.") from e

        self._play = sync_playwright().start()
        self._browser = self._play.chromium.launch(headless=self.headless)
        context_kwargs = {}
        if self.user_agent:
            context_kwargs["user_agent"] = self.user_agent
        self._context = self._browser.new_context(**context_kwargs)
        self.page = self._context.new_page()

    def close(self):
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._play:
                self._play.stop()
        except Exception:
            pass

        self._play = None
        self._browser = None
        self._context = None
        self.page = None

    def search(self, query: str, wait: int = 3) -> str:
        if not self._play:
            self.start()
        url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            consent_btn = self.page.locator("button[aria-label*='Accept']").first
            if consent_btn.is_visible(timeout=3000):
                consent_btn.click()
                self.page.wait_for_timeout(2000)
        except:
            pass
        self.page.wait_for_timeout(3000)
        return self.page.content()

    def _extract_text(self, selector: str) -> str:
        try:
            element = self.page.locator(selector).first
            if element and element.is_visible():
                return element.inner_text().strip()
        except Exception:
            pass
        return ""

    def _extract_name(self) -> str:
        for selector in ["h1", "h2", "h3", "div[aria-level='1']", "div[role='heading']"]:
            text = self._extract_text(selector)
            if text:
                return text
        return ""

    def _normalize_text(self, value: str) -> str:
        return " ".join(value.lower().strip().split())

    def _extract_phone(self) -> str:
        try:
            phone_link = self.page.locator('a[href^="tel:"]')
            if phone_link.count() > 0:
                href = phone_link.first.get_attribute("href")
                if href and href.startswith("tel:"):
                    return href.replace("tel:", "").strip()
        except Exception:
            pass
        try:
            phone_button = self.page.locator('button[aria-label*="phone"]')
            if phone_button.count() > 0:
                return phone_button.first.inner_text().strip()
        except Exception:
            pass
        return ""

    def _extract_address(self) -> str:
        address = self._extract_text('button[data-item-id="address"]')
        if address:
            return address
        return self._extract_text('button[aria-label*="Address"]')

    def __scroll_results(self) -> None:
        try:
            for _ in range(6):
                self.page.mouse.wheel(0, 1200)
                self.page.wait_for_timeout(1200)
        except Exception:
            pass

    def search_places(self, query: str, max_results: int = 100, wait: int = 3) -> List[Dict[str, Any]]:
        self.search(query, wait=wait)
        places: List[Dict[str, Any]] = []
        self.page.wait_for_timeout(2000)
        seen_urls = set()
        attempts = 0
        last_count = 0
        # Keep expanding/scrolling until we have enough results or we've stalled
        while len(seen_urls) < max_results and attempts < 12:
            self.__scroll_results()
            # try clicking a "More places" or "See more" element if present
            try:
                more_btn = self.page.locator("button:has-text('More places')").first
                if more_btn and more_btn.is_visible():
                    more_btn.click()
                    self.page.wait_for_timeout(1500)
            except Exception:
                pass

            results = self.page.locator('div[role="article"]')
            count = results.count()

            # If no new results appeared, increase attempts and break if stalled
            if count == last_count:
                attempts += 1
            else:
                attempts = 0
                last_count = count

            # Collect items up to max_results
            for index in range(count):
                if len(seen_urls) >= max_results:
                    break
                try:
                    card = results.nth(index)
                    # get link/preview url without clicking first when possible
                    try:
                        link = card.locator('a[href*="/place/"]').first
                        url = link.get_attribute('href') if link.count() > 0 else None
                    except Exception:
                        url = None

                    # Skip if we've already seen this url
                    if url and url in seen_urls:
                        continue

                    # Click to open details and capture phone/address
                    try:
                        card.scroll_into_view_if_needed()
                        card.click()
                        self.page.wait_for_timeout(1800)
                    except Exception:
                        pass

                    name = self._extract_name() or self._extract_text('h1') or self._extract_text('h2')
                    phone = self._extract_phone()
                    address = self._extract_address()
                    detail_url = self.page.url

                    record_url = url or detail_url
                    record_key = record_url or self._normalize_text(f"{name}|{address}")
                    if record_key in seen_urls:
                        continue

                    seen_urls.add(record_key)
                    places.append({
                        "name": name,
                        "phone_candidates": [phone] if phone else [],
                        "url": record_url,
                        "detail_location": address,
                    })
                except Exception:
                    continue

            # small wait before next scroll/expand
            self.page.wait_for_timeout(800)

        return places
