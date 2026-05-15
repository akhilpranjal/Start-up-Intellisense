Startup Intelligence — Minimal scaffold

This repository contains a minimal, beginner-friendly scaffold for the "Startup Intelligence Platform":

- FastAPI backend (app/api.py)
- SQLAlchemy models (app/models.py) using a simple local SQLite default
- RQ worker skeleton (workers/worker.py)
- Scrapers and extractors skeletons (scrapers/, extractors/)
- Local embeddings via `sentence-transformers` (embeddings/)
- Streamlit demo UI (ui/streamlit_app.py)
- `docker-compose.yml` for Postgres, Redis and Qdrant

Quickstart (local, minimal):

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

2. Initialize the local DB and run the API:

```bash
python -m app.db && python main.py api
```

3. Run the Streamlit UI:

```bash
python main.py ui
```

For a full local stack with Postgres/Redis/Qdrant:

```bash
docker compose up -d
```

