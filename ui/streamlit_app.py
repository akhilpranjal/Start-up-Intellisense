import streamlit as st
import requests

API_URL = st.secrets.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Startup Intelligence", layout="wide")

st.title("Startup Intelligence")
st.caption("YC scrape -> raw DB -> structure -> embeddings -> Qdrant")


def call_api(method: str, path: str, payload: dict | None = None):
    url = f"{API_URL}{path}"
    if method == "GET":
        return requests.get(url, timeout=30)
    return requests.post(url, json=payload or {}, timeout=300)


top_left, top_mid, top_right = st.columns(3)
try:
    stats = call_api("GET", "/admin/stats").json()
    top_left.metric("Raw rows", stats.get("raw_count", 0))
    top_mid.metric("Structured startups", stats.get("startup_count", 0))
    top_right.metric("API", API_URL)
except Exception as exc:
    st.error(f"Could not load stats: {exc}")
    stats = {"recent_raw": [], "recent_startups": []}

tab_scrape, tab_search, tab_data = st.tabs(["Scrape YC", "Search", "Data"])

with tab_scrape:
    st.subheader("Trigger YC scrape")
    with st.form("scrape_yc_form"):
        max_pages = st.number_input("Pages to scrape", min_value=1, max_value=10, value=1, step=1)
        submitted = st.form_submit_button("Scrape now")
    if submitted:
        try:
            response = call_api("POST", "/scrape/yc", {"max_pages": int(max_pages)})
            st.json(response.json())
        except Exception as exc:
            st.error(f"Scrape request failed: {exc}")

with tab_search:
    st.subheader("Semantic search over Qdrant")
    query = st.text_input("Search query", placeholder="e.g. AI for sales teams")
    if st.button("Search"):
        try:
            response = call_api("POST", "/search", {"query": query})
            st.json(response.json())
        except Exception as exc:
            st.error(f"Search failed: {exc}")

with tab_data:
    left, right = st.columns(2)
    with left:
        st.subheader("Recent raw rows")
        st.dataframe(stats.get("recent_raw", []), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Recent startups")
        st.dataframe(stats.get("recent_startups", []), use_container_width=True, hide_index=True)
