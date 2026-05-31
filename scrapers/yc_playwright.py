from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_yc_companies(max_pages: int = 1):
    """Scrape YC companies listing pages (best-effort). Returns list of dicts."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i in range(1, max_pages + 1):
            url = f"https://www.ycombinator.com/companies?page={i}"
            page.goto(url, timeout=30000)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Best-effort selectors: company cards often have 'article' tags or role=article
            cards = soup.find_all(["article", "li"])
            for c in cards:
                # try common patterns
                name = None
                link = None
                desc = None
                h = c.find(["h3", "h2"]) or c.find(class_=lambda x: x and "name" in x)
                if h:
                    name = h.get_text(strip=True)
                a = c.find("a", href=True)
                if a:
                    link = a["href"]
                p = c.find("p")
                if p:
                    desc = p.get_text(strip=True)

                if name or desc:
                    results.append({"name": name or "", "website": link or "", "description": desc or "", "source": "yc"})

        browser.close()

    return results


if __name__ == "__main__":
    out = scrape_yc_companies(max_pages=1)
    print(out[:10])
