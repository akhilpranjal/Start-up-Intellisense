from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.config import get_settings


@dataclass
class YCCompany:
    """Description:
Represent one scraped YC company record.
Input Description:
The dataclass fields are filled from scraped page data.
Output Description:
Provides a small record object with an as_dict helper.
"""
    yc_slug: str
    name: str
    description: str = ""
    tags: list[str] | None = None
    batch: str = ""
    website: str = ""
    location: str = ""
    company_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Description:
Convert the dataclass into a plain dictionary.
Input Description:
No direct inputs beyond the current instance state.
Output Description:
Returns a dictionary ready for storage.
"""
        return {
            "yc_slug": self.yc_slug,
            "name": self.name,
            "description": self.description,
            "tags": self.tags or [],
            "batch": self.batch,
            "website": self.website,
            "location": self.location,
            "company_url": self.company_url,
        }


def _slug_from_url(url: str) -> str:
    """Description:
Derive a YC slug from a URL path.
Input Description:
url is the company link or href.
Output Description:
Returns the final URL segment or a fallback slug.
"""
    slug = url.rstrip("/").split("/")[-1]
    return slug or "company"


def _parse_company_cards(html: str, base_url: str) -> list[YCCompany]:
    """Description:
Parse YC company cards from HTML.
Input Description:
html is the fetched page content and base_url resolves relative links.
Output Description:
Returns a list of YCCompany records.
"""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    companies: list[YCCompany] = []

    for anchor in soup.select('a[href*="/companies/"]'):
        href = anchor.get("href") or ""
        if not href:
            continue
        company_url = urljoin(base_url, href)
        yc_slug = _slug_from_url(href)
        if yc_slug in seen:
            continue
        seen.add(yc_slug)

        text = " ".join(anchor.get_text(" ", strip=True).split())
        if not text:
            continue

        name = text.split(" - ")[0].split(" | ")[0].strip()
        description = ""
        parent = anchor.parent
        if parent:
            sibling_text = " ".join(parent.get_text(" ", strip=True).split())
            if sibling_text and sibling_text != name:
                description = sibling_text.replace(name, "", 1).strip(" -|:")

        companies.append(
            YCCompany(
                yc_slug=yc_slug,
                name=name or yc_slug,
                description=description,
                tags=[],
                batch="",
                website="",
                location="",
                company_url=company_url,
            )
        )

    return companies


async def _crawl_html(url: str) -> str:
    """Description:
Fetch YC HTML with Crawl4AI when available.
Input Description:
url is the page to crawl.
Output Description:
Returns HTML, cleaned HTML, markdown, or an empty string.
"""
    try:
        from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
    except Exception:
        return ""

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
        if getattr(result, "html", None):
            return result.html
        if getattr(result, "cleaned_html", None):
            return result.cleaned_html
        if getattr(result, "markdown", None):
            return result.markdown
    return ""


async def scrape_yc_companies() -> list[dict[str, Any]]:
    """Description:
Scrape YC companies and convert them to plain dictionaries.
Input Description:
No direct inputs.
Output Description:
Returns a list of scraped company dictionaries.
"""
    settings = get_settings()
    html = await _crawl_html(settings.yc_url)
    if not html:
        return []
    companies = _parse_company_cards(html, settings.yc_url)
    return [company.as_dict() for company in companies]
