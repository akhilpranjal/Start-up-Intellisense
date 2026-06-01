from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from .config import get_settings
from .embeddings import EMBEDDING_DIMENSION


def get_client() -> QdrantClient:
    """Description:
Create a Qdrant client from the current settings.
Input Description:
No direct inputs.
Output Description:
Returns a configured QdrantClient instance.
"""
    settings = get_settings()
    if settings.qdrant_api_key:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    """Description:
Create the configured Qdrant collection when needed.
Input Description:
No direct inputs.
Output Description:
Returns nothing after ensuring the collection exists.
"""
    settings = get_settings()
    client = get_client()
    try:
        client.get_collection(settings.qdrant_collection)
        return
    except Exception:
        pass
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=rest.VectorParams(size=EMBEDDING_DIMENSION, distance=rest.Distance.COSINE),
    )


def upsert_company_vector(company: dict[str, Any], embedding: list[float]) -> None:
    """Description:
Store one company's vector and payload in Qdrant.
Input Description:
company contains row data and embedding contains the vector values.
Output Description:
Returns nothing after upserting the point.
"""
    settings = get_settings()
    client = get_client()
    payload = {
        "yc_slug": company.get("yc_slug"),
        "name": company.get("name"),
        "description": company.get("description"),
        "batch": company.get("batch"),
        "website": company.get("website"),
        "location": company.get("location"),
        "tags": company.get("tags") or [],
        "problem_domain": company.get("problem_domain"),
        "tech_stack": company.get("tech_stack") or [],
        "target_market": company.get("target_market"),
        "one_line_summary": company.get("one_line_summary"),
        "skills": company.get("skills") or [],
        "terms": company.get("terms") or [],
        "cluster_label": company.get("cluster_label"),
        "cluster_name": company.get("cluster_name"),
    }
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[rest.PointStruct(id=str(company.get("yc_slug")), vector=embedding, payload=payload)],
    )


def search_vectors(embedding: list[float], limit: int = 10) -> list[dict[str, Any]]:
    """Description:
Search Qdrant for similar vectors.
Input Description:
embedding is the query vector and limit controls the result count.
Output Description:
Returns a list of scored Qdrant matches.
"""
    settings = get_settings()
    client = get_client()
    try:
        hits = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=embedding,
            limit=limit,
            with_payload=True,
        )
    except Exception:
        return []
    results: list[dict[str, Any]] = []
    for hit in hits:
        results.append(
            {
                "score": float(hit.score),
                "payload": dict(hit.payload or {}),
            }
        )
    return results


def load_all_points() -> list[dict[str, Any]]:
    """Description:
Load every point from the Qdrant collection.
Input Description:
No direct inputs.
Output Description:
Returns a list of stored points with payloads and vectors.
"""
    settings = get_settings()
    client = get_client()
    offset = None
    points: list[dict[str, Any]] = []
    try:
        while True:
            batch, offset = client.scroll(
                collection_name=settings.qdrant_collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            for item in batch:
                points.append(
                    {
                        "id": item.id,
                        "payload": dict(item.payload or {}),
                        "vector": list(item.vector or []),
                    }
                )
            if offset is None:
                break
    except Exception:
        return []
    return points
