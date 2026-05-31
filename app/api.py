from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
import os
import redis
from rq import Queue

from . import db
from .models import RawScrape, Startup
from embeddings.local_embedder import embed_texts
from qdrant_client import QdrantClient

app = FastAPI(title="Startup Intelligence Platform - API")


@app.on_event("startup")
def startup() -> None:
    db.init_db()


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


class IngestRequest(BaseModel):
    source: str
    raw_text: str
    metadata: dict | None = None


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@app.post("/ingest")
def ingest(req: IngestRequest, db_session=Depends(get_db)):
    # persist raw scrape
    rec = RawScrape(source=req.source, raw_text=req.raw_text, meta=req.metadata or {})
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)

    # enqueue background processing
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_conn = redis.from_url(redis_url, protocol=2)
        q = Queue("default", connection=redis_conn)
        q.enqueue("workers.tasks.process_raw", rec.id)
        return {"status": "enqueued", "raw_id": rec.id}
    except Exception:
        # Fallback for environments without a compatible Redis/RQ setup.
        from workers.tasks import process_raw

        out = process_raw(rec.id)
        return {"status": "processed_inline", "raw_id": rec.id, "result": out}


class SearchRequest(BaseModel):
    query: str


class ReindexRequest(BaseModel):
    collection: str | None = None


class ScrapeRequest(BaseModel):
    max_pages: int = 1


def _serialize_raw(row: RawScrape) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "scraped_at": row.scraped_at.isoformat() if row.scraped_at else None,
        "raw_text": row.raw_text,
        "metadata": row.meta or {},
    }


def _serialize_startup(row: Startup) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "source": row.source,
        "metadata": row.meta or {},
    }


@app.post("/search")
def search(req: SearchRequest):
    # embed the query
    vecs = embed_texts([req.query])
    qvec = vecs[0].tolist()

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "startups")

    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, check_compatibility=False)
        hits = client.search(collection_name=collection, query_vector=qvec, limit=10)
        results = []
        for h in hits:
            results.append({"id": h.id, "score": h.score, "payload": h.payload})
        return {"query": req.query, "results": results}
    except Exception:
        # If Qdrant not available, return empty results
        return {"query": req.query, "results": []}


@app.get("/admin/stats")
def admin_stats(db_session=Depends(get_db)):
    raw_count = db_session.query(RawScrape).count()
    startup_count = db_session.query(Startup).count()
    recent_raw = db_session.query(RawScrape).order_by(RawScrape.id.desc()).limit(5).all()
    recent_startups = db_session.query(Startup).order_by(Startup.id.desc()).limit(5).all()
    return {
        "raw_count": raw_count,
        "startup_count": startup_count,
        "recent_raw": [_serialize_raw(row) for row in recent_raw],
        "recent_startups": [_serialize_startup(row) for row in recent_startups],
    }


@app.post("/scrape/yc")
def scrape_yc(req: ScrapeRequest):
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_conn = redis.from_url(redis_url, protocol=2)
        q = Queue("default", connection=redis_conn)
        job = q.enqueue("workers.tasks.scrape_and_process_yc", req.max_pages)
        return {"status": "enqueued", "job_id": job.id, "max_pages": req.max_pages}
    except Exception:
        from workers.tasks import scrape_and_process_yc

        out = scrape_and_process_yc(req.max_pages)
        return {"status": "processed_inline", "max_pages": req.max_pages, "result": out}


@app.post("/admin/reindex")
def admin_reindex(req: ReindexRequest, authorization: str | None = Header(None)):
    # simple admin token protection: set ADMIN_TOKEN env var to require it
    admin_token = os.getenv("ADMIN_TOKEN")
    if admin_token:
        if not authorization:
            raise HTTPException(status_code=401, detail="missing authorization header")
        token = authorization.split()[-1]
        if token != admin_token:
            raise HTTPException(status_code=403, detail="invalid admin token")

    # enqueue a full reindex job
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_conn = redis.from_url(redis_url, protocol=2)
        q = Queue("default", connection=redis_conn)
        q.enqueue("workers.tasks.reindex_all", req.collection)
        return {"status": "reindex_enqueued", "collection": req.collection}
    except Exception:
        from workers.tasks import reindex_all

        out = reindex_all(req.collection)
        return {"status": "reindex_inline", "collection": req.collection, "result": out}


def start():
    import uvicorn

    uvicorn.run("app.api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
