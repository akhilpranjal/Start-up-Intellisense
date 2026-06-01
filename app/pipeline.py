from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

import hdbscan
import numpy as np

from .db import (
    companies_missing_embedding,
    companies_missing_extraction,
    count_companies,
    ensure_schema,
    latest_companies,
    update_cluster,
    update_embedding,
    update_extracted_fields,
    upsert_scraped_company,
)
from .embeddings import embed_text
from .llm import extract_company_fields, name_cluster
from .vector_store import ensure_collection, load_all_points, upsert_company_vector
from scrapers.yc import scrape_yc_companies


def _company_slug(company: dict[str, Any]) -> str:
    """Description:
Create a stable slug for a company row.
Input Description:
company is the scraped company dictionary.
Output Description:
Returns a lowercase slug string.
"""
    return str(company.get("yc_slug") or company.get("slug") or company.get("name") or "company").lower().replace(" ", "-")


def scrape_yc_once() -> int:
    """Description:
Scrape YC companies and store them in Postgres.
Input Description:
No direct inputs.
Output Description:
Returns the number of scraped companies.
"""
    ensure_schema()
    companies = asyncio.run(scrape_yc_companies())
    for company in companies:
        company["yc_slug"] = _company_slug(company)
        upsert_scraped_company(company)
    return len(companies)


def extract_companies() -> int:
    """Description:
Run extraction for rows missing structured fields.
Input Description:
No direct inputs.
Output Description:
Returns the number of processed company rows.
"""
    ensure_schema()
    rows = companies_missing_extraction()
    count = 0
    for row in rows:
        extracted = extract_company_fields(
            name=row.get("name", ""),
            description=row.get("description", ""),
            tags=row.get("tags") or [],
        )
        update_extracted_fields(row["yc_slug"], extracted)
        count += 1
    return count


def embed_companies() -> int:
    """Description:
Create embeddings for rows missing vectors.
Input Description:
No direct inputs.
Output Description:
Returns the number of embedded company rows.
"""
    ensure_schema()
    ensure_collection()
    rows = companies_missing_embedding()
    count = 0
    for row in rows:
        summary = row.get("one_line_summary") or row.get("description") or row.get("name") or ""
        embedding = embed_text(summary)
        update_embedding(row["yc_slug"], embedding)
        upsert_company_vector(row, embedding)
        count += 1
    return count


def cluster_trends(min_cluster_size: int = 5) -> dict[str, Any]:
    """Description:
Cluster stored vectors and persist labels.
Input Description:
min_cluster_size controls the HDBSCAN minimum cluster size.
Output Description:
Returns a summary dictionary with cluster metadata and total count.
"""
    ensure_schema()
    ensure_collection()
    points = load_all_points()
    if not points:
        return {"clusters": [], "count": 0}

    vectors = np.array([point["vector"] for point in points], dtype=float)
    if len(points) < 2:
        labels = np.array([-1 for _ in points], dtype=int)
    else:
        real_min_size = max(2, min(min_cluster_size, len(points)))
        clusterer = hdbscan.HDBSCAN(min_cluster_size=real_min_size, min_samples=None)
        labels = clusterer.fit_predict(vectors)

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for point, label in zip(points, labels):
        payload = dict(point.get("payload") or {})
        payload["yc_slug"] = payload.get("yc_slug") or str(point.get("id"))
        grouped[int(label)].append(payload)

    summary: list[dict[str, Any]] = []
    for label, members in grouped.items():
        cluster_name = name_cluster(members, label)
        for member in members:
            update_cluster(member["yc_slug"], label, cluster_name)
        summary.append({"cluster_label": label, "cluster_name": cluster_name, "count": len(members)})

    summary.sort(key=lambda item: (-item["count"], item["cluster_label"]))
    return {"clusters": summary, "count": len(points)}


def dashboard_summary() -> dict[str, Any]:
    """Description:
Return a small summary payload for the UI.
Input Description:
No direct inputs.
Output Description:
Returns latest companies and the total company count.
"""
    return {
        "latest_companies": latest_companies(15),
        "companies_total": count_companies(),
    }
