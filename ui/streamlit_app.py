from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import cluster_groups, count_companies, latest_companies, search_text, top_values  # noqa: E402
from app.embeddings import embed_text  # noqa: E402
from app.vector_store import search_vectors  # noqa: E402


st.set_page_config(page_title="Startup Intellisense", layout="wide")


def _friendly_card(item: dict[str, Any]) -> str:
    """Description:
Format one company payload for display in Streamlit.
Input Description:
item is a company dictionary with optional summary fields.
Output Description:
Returns a markdown string for the dashboard.
"""
    name = item.get("name") or "Unknown startup"
    summary = item.get("one_line_summary") or item.get("description") or "No summary yet."
    domain = item.get("problem_domain") or ""
    market = item.get("target_market") or ""
    cluster_name = item.get("cluster_name") or "Unclustered"
    parts = [part for part in [domain, market] if part]
    suffix = f" ({', '.join(parts)})" if parts else ""
    return f"**{name}** - {summary}{suffix}  \nCluster: {cluster_name}"


st.title("Startup Intellisense")
st.caption("Simple YC startup search, clustering, and trend tracking.")

col1, col2, col3 = st.columns(3)
col1.metric("Companies", count_companies())
col2.metric("Clusters", len(cluster_groups()))
col3.metric("Latest rows", len(latest_companies(15)))

tab_search, tab_clusters, tab_trends, tab_latest = st.tabs([
    "Semantic search",
    "Trend clusters",
    "Trends",
    "Latest companies",
])

with tab_search:
    query = st.text_input("Search startups", placeholder="e.g. AI sales copilot for clinics")
    limit = st.slider("Results", 3, 20, 10)
    if query:
        vector = embed_text(query)
        results = search_vectors(vector, limit)
        if not results:
            fallback = search_text(query, limit)
            st.write("No vector matches yet, so here are text matches.")
            for item in fallback:
                st.markdown(_friendly_card(item))
                st.divider()
        else:
            for result in results:
                payload = result.get("payload") or {}
                st.markdown(_friendly_card(payload))
                st.caption(f"Score: {result.get('score', 0):.3f}")
                st.divider()

with tab_clusters:
    clusters = cluster_groups()
    if not clusters:
        st.info("No clusters yet. Run the scrape, extract, embed, and cluster scripts first.")
    else:
        for cluster in clusters:
            with st.expander(f"{cluster['cluster_name']} ({cluster['count']})", expanded=False):
                members = cluster.get("members") or []
                st.write(", ".join(members))

with tab_trends:
    left, right = st.columns(2)
    tech = pd.DataFrame(top_values("tech_stack", 20))
    skills = pd.DataFrame(top_values("skills", 20))
    terms = pd.DataFrame(top_values("terms", 20))

    with left:
        st.subheader("Tech stack breakdown")
        if tech.empty:
            st.info("No tech stack data yet.")
        else:
            st.bar_chart(tech.set_index("label")["count"])

        st.subheader("Trending skills")
        if skills.empty:
            st.info("No skill data yet.")
        else:
            st.bar_chart(skills.set_index("label")["count"])

    with right:
        st.subheader("Trending terms")
        if terms.empty:
            st.info("No term data yet.")
        else:
            st.bar_chart(terms.set_index("label")["count"])

with tab_latest:
    items = latest_companies(15)
    if not items:
        st.info("No companies yet.")
    else:
        st.dataframe(pd.DataFrame(items), use_container_width=True)
