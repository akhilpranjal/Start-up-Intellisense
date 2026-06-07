from __future__ import annotations

import os
import json
import asyncio
import asyncpg

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")

client = Groq(api_key=GROQ_API_KEY)


def build_prompt(companies: list[dict]) -> str:
    company_text = []

    for c in companies:
        company_text.append(
            f"""
Name: {c["name"]}
One Liner: {c["one_liner"] or ""}
Problem Domain: {c["problem_domain"] or ""}
Target Market: {c["target_market"] or ""}
"""
        )

    joined = "\n".join(company_text)

    return f"""
You are analyzing a startup ecosystem cluster.

The following startups belong to the same semantic cluster.

{joined}

Your task:

1. Create a short cluster name (2-5 words)
2. Create a one sentence description
3. Generate 5-10 keywords

Return ONLY valid JSON.

Example:

{{
    "cluster_name": "Developer Infrastructure",
    "description": "Tools and platforms that help software teams build, deploy and operate applications.",
    "keywords": [
        "developer tools",
        "infrastructure",
        "cloud",
        "platform engineering"
    ]
}}
"""


def generate_cluster_metadata(companies: list[dict]):

    prompt = build_prompt(companies)

    response = client.chat.completions.create(
        model=f"{GROQ_MODEL}",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    content = response.choices[0].message.content

    return json.loads(content)


async def get_clusters(conn):

    rows = await conn.fetch(
        """
        SELECT DISTINCT cluster_id
        FROM yc_companies
        WHERE cluster_id IS NOT NULL
        ORDER BY cluster_id
        """
    )

    return [row["cluster_id"] for row in rows]


async def get_cluster_companies(
    conn,
    cluster_id: int,
):

    rows = await conn.fetch(
        """
        SELECT
            name,
            one_liner,
            problem_domain,
            target_market,
            cluster_confidence
        FROM yc_companies
        WHERE cluster_id = $1
        ORDER BY cluster_confidence DESC
        LIMIT 20
        """,
        cluster_id,
    )

    return [dict(row) for row in rows]


async def get_company_count(
    conn,
    cluster_id: int,
):

    return await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM yc_companies
        WHERE cluster_id = $1
        """,
        cluster_id,
    )


async def save_cluster(
    conn,
    cluster_id,
    metadata,
    company_count,
):

    await conn.execute(
        """
        INSERT INTO startup_clusters (
            cluster_id,
            cluster_name,
            description,
            keywords,
            company_count
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5
        )
        ON CONFLICT (cluster_id)
        DO UPDATE SET
            cluster_name = EXCLUDED.cluster_name,
            description = EXCLUDED.description,
            keywords = EXCLUDED.keywords,
            company_count = EXCLUDED.company_count
        """,
        cluster_id,
        metadata["cluster_name"],
        metadata["description"],
        json.dumps(metadata["keywords"]),
        company_count,
    )


async def process_cluster(
    conn,
    cluster_id,
):

    print(f"Processing cluster {cluster_id}")

    companies = await get_cluster_companies(
        conn,
        cluster_id,
    )

    if len(companies) < 3:
        print("Skipping tiny cluster")
        return

    metadata = generate_cluster_metadata(
        companies
    )

    company_count = await get_company_count(
        conn,
        cluster_id,
    )

    await save_cluster(
        conn,
        cluster_id,
        metadata,
        company_count,
    )

    print(
        f"Saved: {metadata['cluster_name']}"
    )


async def main():

    conn = await asyncpg.connect(
        DATABASE_URL
    )

    try:

        clusters = await get_clusters(
            conn
        )

        print(
            f"Found {len(clusters)} clusters"
        )

        for cluster_id in clusters:

            try:
                await process_cluster(
                    conn,
                    cluster_id,
                )

            except Exception as e:
                print(
                    f"Cluster {cluster_id} failed: {e}"
                )

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())