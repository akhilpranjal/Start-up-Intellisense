import streamlit as st
import requests

API_URL = st.secrets.get("API_URL", "http://localhost:8000")

st.title("Startup Intelligence — Demo")

tab = st.tabs(["Semantic Search", "Trending", "Clusters"])

with tab[0]:
    q = st.text_input("Search query")
    if st.button("Search"):
        resp = requests.post(f"{API_URL}/search", json={"query": q})
        st.json(resp.json())

with tab[1]:
    st.write("Trending startups — placeholder")

with tab[2]:
    st.write("Clusters — placeholder")
