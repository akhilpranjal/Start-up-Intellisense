# Startup Intellisense

This repo is intentionally simple.

The whole flow is:

1. Scrape YC company pages once with Crawl4AI and save each company to Postgres.
2. Extract extra fields from the description with Groq and write them back to the same row.
3. Create an embedding from the one-line summary with a free sentence-transformer, store it in Qdrant, and also keep a copy in Postgres.
4. Load the vectors again, cluster them with HDBSCAN, save cluster labels to Postgres, and ask the LLM to name each cluster.

## What you get

- `scripts/scrape_yc.py` for the first scrape.
- `scripts/extract_companies.py` for LLM field extraction.
- `scripts/embed_companies.py` for embeddings and Qdrant upserts.
- `scripts/cluster_trends.py` for HDBSCAN clustering and cluster names.
- `ui/streamlit_app.py` for the dashboard.
- `app/api.py` for a tiny FastAPI layer if you want it.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

You also need these services running somewhere:

- PostgreSQL
- Qdrant

## Environment

Copy [.env.example](.env.example) to `.env` and fill in the values.

Important variables:

- `DATABASE_URL` for Postgres.
- `QDRANT_URL`, `QDRANT_API_KEY`, and `QDRANT_COLLECTION`.
- `GROQ_API_KEY` and `GROQ_MODEL` for extraction and cluster names.
- Embeddings use a local sentence-transformer, so no embedding API key is needed.
- `EXTRACTION_MODE=groq` to use Groq, or `mock` if you just want the pipeline to run with fake extraction.

## Run the scripts

```powershell
python scripts\scrape_yc.py
python scripts\extract_companies.py
python scripts\embed_companies.py
python scripts\cluster_trends.py
```

## Run the app

```powershell
uvicorn app.api:app --host 0.0.0.0 --port 8000
streamlit run ui/streamlit_app.py
```

## Dashboard

The dashboard is kept plain on purpose:

- Semantic search: type a query and see matching startups in friendly language.
- Trend clusters: see which startups belong to which cluster.
- Tech stack breakdown: bar chart of the most common technologies.
- Trending skills: count of the extracted skills field.
- Trending terms: count of the extracted terms field.
- Latest companies: top 15 newest rows.
