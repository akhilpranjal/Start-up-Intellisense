# Startup Intellisense

This project focuses on Y Combinator companies (`scrapers/yc_playwright.py`) via Playwright.

The pipeline:
1. YC scraper fetches company cards.
2. Raw data is persisted (`raw_scrape`) and enqueued to RQ.
3. Worker extracts structure, creates embeddings, deduplicates startups.
4. Embeddings are upserted into Qdrant.
5. API provides semantic search.

## Components

- API: `app/api.py`
- DB models: `app/models.py`
- Worker tasks: `workers/tasks.py`
- YC scraper: `scrapers/yc_playwright.py`
- Scheduler: `scripts/run_scheduler.py`
- Manual scraper CLI: `scripts/run_scraper.py`

## Setup

1. Create and activate virtualenv:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
python -m playwright install
```

## Configuration

Use `.env` in project root.

Required/commonly used keys:
- `REDIS_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY` (blank for local Qdrant)
- `QDRANT_COLLECTION`
- `DATABASE_URL`
- `ADMIN_TOKEN` (optional, secures admin endpoint)
- `GROQ_API_KEY`, `GROQ_MODEL` + `EXTRACTION_MODE=llm` (recommended)

## Run

Start API:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

Start worker:

```bash
rq worker default
```

Run YC scheduler (every 6 hours):

```bash
python scripts/run_scheduler.py
```

Run one YC scrape manually:

```bash
python scripts/run_scraper.py yc 1
```

## Useful endpoints

- `GET /health`
- `POST /ingest`
- `POST /search`
- `POST /admin/reindex` (optionally protected by `ADMIN_TOKEN`)

## Notes
- If you already have DB rows and want them in Qdrant, run:

```bash
python scripts/reindex_qdrant.py
```
