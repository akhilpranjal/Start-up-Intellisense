import os
import json
import asyncio

import asyncpg
from dotenv import load_dotenv
from groq import Groq
from numpy import random


# Configuration
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

if not GROQ_MODEL:
    raise ValueError("GROQ_MODEL not found")


client = Groq(api_key=GROQ_API_KEY)


# Database

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)


async def get_next_batch(conn, batch_size=100):
    return await conn.fetch(
        """
        SELECT
            slug,
            description
        FROM yc_companies
        WHERE
            enrichment_completed = FALSE
            OR problem_domain IS NULL
        ORDER BY slug
        LIMIT $1
        """,
        batch_size,
    )


async def get_remaining_count(conn):
    return await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM yc_companies
        WHERE
            enrichment_completed = FALSE
            OR problem_domain IS NULL
        """
    )


async def update_company(
    conn,
    slug,
    problem_domain,
    target_market
):
    await conn.execute(
        """
        UPDATE yc_companies
        SET
            problem_domain = $1,
            target_market = $2,
            enrichment_completed = TRUE
        WHERE slug = $3
        """,
        problem_domain,
        target_market,
        slug
    )


# LLM Extraction

SYSTEM_PROMPT = """
You are a structured information extraction system.

Return ONLY valid JSON.

Do not include markdown.
Do not include explanations.
Do not include code fences.
"""

USER_PROMPT_TEMPLATE = """
Given the startup description below, extract:

1. problem_domain: A problem domain is the specific real-world area, subject, or field for which you are trying to develop a solution.
2. target_market: A target market is the specific group of consumers or businesses a company aims to sell its products or services to.

Maximum 75 characters for each field.
If it is over 75 characters, summarise to fit within the limit while retaining the core meaning.
If you cannot determine a field, return null for that field.
Return JSON in exactly this format:

{{
  "problem_domain": "...",
  "target_market": "..."
}}

Description:

{description}
"""


def extract_fields(slug: str, description: str):
    response = client.chat.completions.create(
        model=f"{GROQ_MODEL}",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    description=description
                )
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    try:
        data = json.loads(content)

    except json.JSONDecodeError:
        try:
            start = content.find("{")
            end = content.rfind("}") + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON object found")

            data = json.loads(content[start:end])

        except Exception as e:
            print(f"\nJSON PARSE FAILED: {slug}")
            print(content)
            print(e)
            return None

    return {
        "problem_domain": data.get("problem_domain"),
        "target_market": data.get("target_market")
    }


def extract_with_retry(
    slug: str,
    description: str,
    max_retries: int = 3
):
    for attempt in range(max_retries):

        try:
            return extract_fields(slug, description)

        except Exception as e:

            print(
                f"Groq error for {slug} "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            print(e)

            if attempt < max_retries - 1:
                import time
                time.sleep(5)

    return None



# Main Processing Loop

async def process_companies():
    conn = await get_connection()

    try:
        total = await get_remaining_count(conn)

        if total == 0:
            print("No companies need enrichment.")
            return

        print(f"\nFound {total} companies to enrich.\n")

        processed = 0

        while True:

            companies = await get_next_batch(
                conn,
                batch_size=100
            )

            if not companies:
                print("\nAll companies processed.")
                break

            for row in companies:

                processed += 1

                slug = row["slug"]
                description = row["description"]

                print(f"\n[{processed}/{total}] {slug}")

                if not description:
                    print("Skipping: empty description")
                    continue

                try:
                    result = extract_with_retry(
                        slug,
                        description
                    )

                    if not result:
                        print("Skipping due to extraction failure")
                        continue

                    problem_domain = result.get(
                        "problem_domain"
                    )

                    target_market = result.get(
                        "target_market"
                    )

                    print(
                        f"problem_domain={problem_domain}"
                    )

                    print(
                        f"target_market={target_market}"
                    )

                    await update_company(
                        conn,
                        slug,
                        problem_domain,
                        target_market
                    )
                    await asyncio.sleep(random.uniform(1.3, 1.8))

                except Exception as e:
                    print(
                        f"ERROR processing {slug}: {e}"
                    )
                    continue

    finally:
        await conn.close()



# Entry Point

async def main():
    await process_companies()


if __name__ == "__main__":
    asyncio.run(main())