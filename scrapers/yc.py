import asyncio
import asyncpg
import httpx
import json
import html
import os
import random
import re
from urllib.parse import urljoin
from dotenv import load_dotenv

from playwright.async_api import async_playwright

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable not set."
    )


BASE_URL = "https://www.ycombinator.com"
COMPANIES_URL = f"{BASE_URL}/companies"

SCROLL_WAIT_MS = 1500
MAX_NO_GROWTH = 5


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS yc_companies (
    slug TEXT PRIMARY KEY,

    name TEXT,
    one_liner TEXT,
    description TEXT,
    website TEXT,

    batch TEXT,
    batch_code TEXT,

    founded_year INTEGER,
    team_size INTEGER,

    status TEXT,

    location TEXT,
    city TEXT,
    country TEXT,

    linkedin_url TEXT,
    twitter_url TEXT,
    github_url TEXT,

    primary_partner TEXT,

    yc_url TEXT,

    founders_json JSONB,
    tags_json JSONB,

    raw_json JSONB,

    scraped_at TIMESTAMPTZ DEFAULT NOW()
);
"""


UPSERT_SQL = """
INSERT INTO yc_companies (
    slug,
    name,
    one_liner,
    description,
    website,

    batch,
    batch_code,

    founded_year,
    team_size,

    status,

    location,
    city,
    country,

    linkedin_url,
    twitter_url,
    github_url,

    primary_partner,

    yc_url,

    founders_json,
    tags_json,

    raw_json,

    scraped_at
)
VALUES (
    $1,$2,$3,$4,$5,
    $6,$7,
    $8,$9,
    $10,
    $11,$12,$13,
    $14,$15,$16,
    $17,
    $18,
    $19,$20,
    $21,
    NOW()
)
ON CONFLICT (slug)
DO UPDATE SET
    name = EXCLUDED.name,
    one_liner = EXCLUDED.one_liner,
    description = EXCLUDED.description,
    website = EXCLUDED.website,

    batch = EXCLUDED.batch,
    batch_code = EXCLUDED.batch_code,

    founded_year = EXCLUDED.founded_year,
    team_size = EXCLUDED.team_size,

    status = EXCLUDED.status,

    location = EXCLUDED.location,
    city = EXCLUDED.city,
    country = EXCLUDED.country,

    linkedin_url = EXCLUDED.linkedin_url,
    twitter_url = EXCLUDED.twitter_url,
    github_url = EXCLUDED.github_url,

    primary_partner = EXCLUDED.primary_partner,

    yc_url = EXCLUDED.yc_url,

    founders_json = EXCLUDED.founders_json,
    tags_json = EXCLUDED.tags_json,

    raw_json = EXCLUDED.raw_json,

    scraped_at = NOW();
"""


async def create_schema(conn):
    await conn.execute(CREATE_TABLE_SQL)


async def load_existing_slugs(conn):
    rows = await conn.fetch(
        "SELECT slug FROM yc_companies"
    )
    return {r["slug"] for r in rows}


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


async def save_company(conn, record):

    await conn.execute(
        UPSERT_SQL,

        record["slug"],
        record["name"],
        record["one_liner"],
        record["description"],
        record["website"],

        record["batch"],
        record["batch_code"],

        record["founded_year"],
        record["team_size"],

        record["status"],

        record["location"],
        record["city"],
        record["country"],

        record["linkedin_url"],
        record["twitter_url"],
        record["github_url"],

        record["primary_partner"],

        record["yc_url"],

        json.dumps(
            record["founders_json"]
        ),
        json.dumps(
            record["tags_json"]
        ),

        json.dumps(
            record["raw_json"]
        ),
    )


async def scrape_company(
    client,
    conn,
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

            await save_company(
                conn,
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

    conn = await asyncpg.connect(
        DATABASE_URL
    )

    await create_schema(conn)

    existing_slugs = (
        await load_existing_slugs(conn)
    )

    urls = await collect_company_urls()

    urls_to_scrape = []

    for url in urls:

        slug = url.rstrip("/").split("/")[-1]

        if slug not in existing_slugs:
            urls_to_scrape.append(url)

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

        total = len(urls_to_scrape)

        for i, url in enumerate(
            urls_to_scrape,
            start=1
        ):

            await scrape_company(
                client,
                conn,
                url,
                i,
                total
            )

            await asyncio.sleep(
                random.uniform(
                    1.0,
                    4.0
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

    await conn.close()

    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())