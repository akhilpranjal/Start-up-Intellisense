from __future__ import annotations

from fastapi import FastAPI, Query

from .db import cluster_groups, count_companies, latest_companies, search_text, top_values
from .embeddings import embed_text
from .vector_store import search_vectors


app = FastAPI(title="Startup Intellisense", version="0.1.0")


@app.get("/health")
def health() -> dict[str, object]:
    """Description:
Return a minimal health payload for the API.
Input Description:
No direct inputs.
Output Description:
Returns a dictionary with the service status and company count.
"""
    return {"ok": True, "companies": count_companies()}


@app.get("/companies/latest")
def companies_latest(limit: int = Query(default=15, ge=1, le=50)) -> dict[str, object]:
    """Description:
Return the newest companies for the dashboard.
Input Description:
limit controls how many records to return.
Output Description:
Returns a dictionary with a list of company rows under items.
"""
    return {"items": latest_companies(limit)}


@app.get("/search")
def search(query: str, limit: int = Query(default=10, ge=1, le=25)) -> dict[str, object]:
    """Description:
Search startups by vector similarity or text fallback.
Input Description:
query is the user search text and limit controls the result count.
Output Description:
Returns a dictionary with the query and matching company items.
"""
    vector = embed_text(query)
    results = search_vectors(vector, limit)
    if results:
        return {"query": query, "items": results}
    return {"query": query, "items": search_text(query, limit)}


@app.get("/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    """Description:
Return the dashboard summary payload.
Input Description:
No direct inputs.
Output Description:
Returns counts and grouped data for the dashboard overview.
"""
    return {
        "total_companies": count_companies(),
        "latest_companies": latest_companies(15),
        "clusters": cluster_groups(),
        "tech_stack": top_values("tech_stack", 20),
        "skills": top_values("skills", 20),
        "terms": top_values("terms", 20),
    }


@app.get("/dashboard/clusters")
def dashboard_clusters() -> dict[str, object]:
    """Description:
Return cluster group summaries.
Input Description:
No direct inputs.
Output Description:
Returns a dictionary containing grouped cluster records.
"""
    return {"items": cluster_groups()}


@app.get("/dashboard/tech-stack")
def dashboard_tech_stack() -> dict[str, object]:
    """Description:
Return the most common tech stack values.
Input Description:
No direct inputs.
Output Description:
Returns a dictionary containing ranked tech stack labels.
"""
    return {"items": top_values("tech_stack", 20)}


@app.get("/dashboard/skills")
def dashboard_skills() -> dict[str, object]:
    """Description:
Return the most common extracted skills.
Input Description:
No direct inputs.
Output Description:
Returns a dictionary containing ranked skill labels.
"""
    return {"items": top_values("skills", 20)}


@app.get("/dashboard/terms")
def dashboard_terms() -> dict[str, object]:
    """Description:
Return the most common extracted terms.
Input Description:
No direct inputs.
Output Description:
Returns a dictionary containing ranked term labels.
"""
    return {"items": top_values("terms", 20)}
