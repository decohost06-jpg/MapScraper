import re
from typing import List, Dict
from bs4 import BeautifulSoup


PHONE_RE = re.compile(r"(\+?\d[\d\-\s\(\)]{6,}\d)")


def extract_phone(text: str) -> List[str]:
    return PHONE_RE.findall(text)


def create_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def parse_places_from_html(html: str) -> List[Dict]:
    """Very small parser that extracts place name, possible phone found in nearby text, and a url if present.

    This is intentionally minimal; real-world selectors need to be adjusted.
    """
    soup = create_soup(html)
    results = []

    # Try to find place anchors that include '/place/' in the href
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/place/" in href:
            name = a.get_text(strip=True)
            container = a.find_parent()
            context_text = container.get_text(separator=" ", strip=True) if container else a.get_text(" ")
            phones = extract_phone(context_text)
            results.append({
                "name": name,
                "phone_candidates": phones,
                "url": href,
            })

    # Fallback: look for role=article tiles
    if not results:
        for article in soup.select("div[role=article]"):
            name_tag = article.find(lambda tag: tag.name in ["h3", "h4"])
            name = name_tag.get_text(strip=True) if name_tag else article.get_text(strip=True)[:60]
            phones = extract_phone(article.get_text(" ", strip=True))
            results.append({"name": name, "phone_candidates": phones, "url": None})

    return results
