from __future__ import annotations

import os
import asyncio

import asyncpg

from dotenv import load_dotenv

from groq import Groq

from qdrant_client import QdrantClient

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

COLLECTION_NAME = "yc_startups"

TOP_K_QDRANT = 50
TOP_K_RERANK = 10

embed_model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5"
)

reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


# EMBED QUERY
def embed_query(query: str):

    vector = embed_model.encode(
        query,
        normalize_embeddings=True,
    )

    return vector.tolist()


# SEARCH QDRANT
def qdrant_search(
    query_vector,
):

    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=TOP_K_QDRANT,
        with_payload=True,
    )

    return hits


# RERANK
def rerank_results(
    query: str,
    hits,
):

    pairs = []

    for hit in hits:

        payload = hit.payload

        text = f"""
        {payload.get("name","")}

        {payload.get("one_liner","")}

        {payload.get("problem_domain","")}

        {payload.get("target_market","")}

        {payload.get("description","")}
        """

        pairs.append(
            (
                query,
                text,
            )
        )

    scores = reranker.predict(
        pairs
    )

    combined = list(
        zip(
            hits,
            scores,
        )
    )

    combined.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    return combined[:TOP_K_RERANK]



# METADATA LOOKUP
async def fetch_company_details(
    conn,
    slugs,
):

    rows = await conn.fetch(
        """
        SELECT
            slug,
            name,
            website,
            one_liner,
            problem_domain,
            target_market,
            cluster_id
        FROM yc_companies
        WHERE slug = ANY($1)
        """,
        slugs,
    )

    return {
        row["slug"]: dict(row)
        for row in rows
    }



# EXPLAIN MATCHES
def explain_match(
    query,
    company,
):

    prompt = f"""
User Query:

{query}

Company:

Name:
{company["name"]}

One Liner:
{company["one_liner"]}

Problem Domain:
{company["problem_domain"]}

Target Market:
{company["target_market"]}

Explain in one sentence
why this company is relevant.

Return only the explanation.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )



# MAIN SEARCH FUNCTION
async def search(
    query: str,
):

    query_vector = embed_query(
        query
    )

    hits = qdrant_search(
        query_vector
    )

    reranked = rerank_results(
        query,
        hits,
    )

    slugs = [
        item[0].payload["slug"]
        for item in reranked
    ]

    conn = await asyncpg.connect(
        DATABASE_URL
    )

    try:

        companies = await fetch_company_details(
            conn,
            slugs,
        )

    finally:
        await conn.close()

    results = []

    for hit, score in reranked:

        slug = hit.payload["slug"]

        company = companies.get(
            slug
        )

        if not company:
            continue

        explanation = explain_match(
            query,
            company,
        )

        results.append(
            {
                "name":
                    company["name"],

                "website":
                    company["website"],

                "score":
                    round(
                        float(score),
                        4
                    ),

                "problem_domain":
                    company["problem_domain"],

                "target_market":
                    company["target_market"],

                "explanation":
                    explanation,
            }
        )

    return results



# MAIN FUNCTION
async def main():

    query = input(
        "Search: "
    )

    results = await search(
        query
    )

    for r in results:

        print()

        print(
            "=" * 60
        )

        print(
            r["name"]
        )

        print(
            r["score"]
        )

        print(
            r["website"]
        )

        print(
            r["explanation"]
        )


if __name__ == "__main__":
    asyncio.run(main())