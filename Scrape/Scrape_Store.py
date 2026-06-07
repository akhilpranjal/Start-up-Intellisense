import asyncio
import httpx
import json
import html
import os
import random
import re

from urllib.parse import urljoin

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from Scrape.PostgreSchema import YCCompanyDB

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set"
    )

BASE_URL = "https://www.ycombinator.com"
COMPANIES_URL = f"{BASE_URL}/companies"

SCROLL_WAIT_MS = 1500
MAX_NO_GROWTH = 5


async def collect_company_urls():
    print("\n[1/3] Collecting company URLs...\n")

    urls = set()

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        await page.goto(
            COMPANIES_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        previous_count = 0
        no_growth_count = 0

        while True:

            links = await page.locator(
                'a[href^="/companies/"]'
            ).evaluate_all(
                """
                els => els.map(
                    e => e.getAttribute('href')
                )
                """
            )

            for href in links:

                if not href:
                    continue

                if href.startswith("/companies/"):

                    path = href.split("?")[0]

                    if path.count("/") == 2:
                        urls.add(
                            urljoin(BASE_URL, path)
                        )

            current_count = len(urls)

            print(
                f"Found {current_count} URLs..."
            )

            if current_count == previous_count:
                no_growth_count += 1
            else:
                no_growth_count = 0

            if no_growth_count >= MAX_NO_GROWTH:
                break

            previous_count = current_count

            await page.mouse.wheel(0, 10000)

            await page.wait_for_timeout(
                SCROLL_WAIT_MS
            )

        await browser.close()

    print(
        f"\nCollected {len(urls)} unique company URLs.\n"
    )

    return sorted(urls)


def extract_data_page(html_text):

    m = re.search(
        r'data-page="(.*?)"',
        html_text,
        re.DOTALL
    )

    if not m:
        return None

    encoded = m.group(1)

    decoded = html.unescape(encoded)

    return json.loads(decoded)


def build_record(company):

    partner = company.get(
        "primary_group_partner"
    )

    return {
        "slug": company.get("slug"),
        "name": company.get("name"),
        "one_liner": company.get("one_liner"),
        "description": company.get(
            "long_description"
        ),
        "website": company.get("website"),

        "batch": company.get("batch_name"),
        "batch_code": company.get("batch"),

        "founded_year": company.get(
            "year_founded"
        ),
        "team_size": company.get(
            "team_size"
        ),

        "status": company.get(
            "ycdc_status"
        ),

        "location": company.get(
            "location"
        ),
        "city": company.get("city"),
        "country": company.get(
            "country"
        ),

        "linkedin_url": company.get(
            "linkedin_url"
        ),
        "twitter_url": company.get(
            "twitter_url"
        ),
        "github_url": company.get(
            "github_url"
        ),

        "primary_partner":
            partner.get("full_name")
            if partner
            else None,

        "yc_url": company.get(
            "ycdc_url"
        ),

        "founders_json":
            company.get("founders", []),

        "tags_json":
            company.get("tags", []),

        "raw_json": company
    }


async def scrape_company(
    client,
    db,
    url,
    index,
    total
):

    for attempt in range(3):

        try:

            r = await client.get(
                url,
                timeout=30
            )

            r.raise_for_status()

            page_data = extract_data_page(
                r.text
            )

            if not page_data:
                raise RuntimeError(
                    "data-page missing"
                )

            company = page_data[
                "props"
            ]["company"]

            record = build_record(
                company
            )

            await db.save_company(
                record
            )

            print(
                f"[{index}/{total}] "
                f"{record['slug']}"
            )

            return True

        except Exception as e:

            print(
                f"Retry {attempt+1}/3 "
                f"{url}"
            )

            await asyncio.sleep(
                random.uniform(2, 5)
            )

    print(f"FAILED: {url}")
    return False


async def main():

    db = YCCompanyDB(
        DATABASE_URL
    )

    await db.connect()

    await db.create_schema()

    existing_slugs = (
        await db.load_existing_slugs()
    )

    urls = await collect_company_urls()

    urls_to_scrape = []

    for url in urls:

        slug = (
            url.rstrip("/")
            .split("/")[-1]
        )

        if slug not in existing_slugs:
            urls_to_scrape.append(
                url
            )

    print(
        f"Need to scrape "
        f"{len(urls_to_scrape)} companies."
    )

    headers = {
        "User-Agent":
        (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/137.0.0.0 "
            "Safari/537.36"
        )
    }

    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True
    ) as client:

        total = len(
            urls_to_scrape
        )

        for i, url in enumerate(
            urls_to_scrape,
            start=1
        ):

            await scrape_company(
                client,
                db,
                url,
                i,
                total
            )

            await asyncio.sleep(
                random.uniform(
                    1,
                    4
                )
            )

            if i % 50 == 0:

                pause = random.uniform(
                    2,
                    5
                )

                print(
                    f"\nLong pause "
                    f"{pause:.1f}s\n"
                )

                await asyncio.sleep(
                    pause
                )

    await db.close()

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())