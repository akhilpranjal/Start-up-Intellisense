from app.db import SessionLocal
from app.models import RawScrape, Startup
from scrapers.base import persist_raw
from scrapers.yc_playwright import scrape_yc_companies
from extractors.mock_extractor import extract_structured
from embeddings.local_embedder import embed_texts
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from qdrant_client.http import models
from qdrant_client.http.models import VectorParams, Distance
from rapidfuzz import fuzz


def _qdrant_unavailable_error(operation: str, exc: Exception) -> dict:
    return {"status": "qdrant_unavailable", "operation": operation, "error": str(exc)}


def _dedupe_and_merge(db, name: str, source: str, metadata: dict, embedding: list):
    # Try matching by name first, then by website if present
    website = metadata.get("url") or (metadata.get("website") if metadata else None)
    existing = None
    if name:
        existing = db.query(Startup).filter(Startup.name == name).first()
    if not existing and website:
        existing = db.query(Startup).filter(Startup.meta["website"].as_string() == website).first() if hasattr(Startup.meta, "as_string") else None

    # Fuzzy name matching if exact didn't find anything
    if not existing and name:
        candidates = db.query(Startup.id, Startup.name).all()
        best = (None, 0)
        for cid, cname in candidates:
            if not cname:
                continue
            score = fuzz.token_sort_ratio(name.lower(), (cname or "").lower())
            if score > best[1]:
                best = (cid, score)
        # threshold: 85
        if best[0] and best[1] >= 85:
            existing = db.query(Startup).filter(Startup.id == best[0]).first()

    if not existing:
        new = Startup(name=name or "", source=source, meta={"sources": [source], "merged": metadata, "embedding": embedding})
        db.add(new)
        db.commit()
        db.refresh(new)
        return new.id

    # Merge metadata
    merged = existing.meta or {}
    merged_sources = merged.get("sources", [])
    if source not in merged_sources:
        merged_sources.append(source)
    merged["sources"] = merged_sources
    # naive merge of extracted fields
    merged["merged"] = {**merged.get("merged", {}), **(metadata or {})}
    merged["embedding"] = embedding
    existing.meta = merged
    db.commit()
    return existing.id


def process_raw(raw_id: int):
    """Background task: load RawScrape, extract structured fields, compute embedding, upsert Startup with deduplication."""
    db = SessionLocal()
    try:
        raw = db.query(RawScrape).filter(RawScrape.id == raw_id).first()
        if not raw:
            return {"error": "raw not found"}

        # Extraction: use LLM extractor if requested via env, otherwise mock
        extraction_mode = os.getenv("EXTRACTION_MODE", "llm")
        if extraction_mode == "llm":
            try:
                from extractors.llm_extractor import extract_structured_llm

                extracted = extract_structured_llm(raw.raw_text or "", metadata=raw.meta or {})
            except Exception:
                extracted = extract_structured(raw.raw_text or "")
        else:
            extracted = extract_structured(raw.raw_text or "")

        # compute embedding for the combined text
        vec = embed_texts([raw.raw_text or ""])  # returns numpy array
        embedding = vec[0].tolist()

        # derive a name for deduplication
        name = extracted.get("startup_name") or (raw.meta or {}).get("name") or (raw.meta or {}).get("title") or ""

        merged_metadata = {**(raw.meta or {}), **(extracted or {})}

        startup_id = _dedupe_and_merge(db, name=name, source=raw.source, metadata=merged_metadata, embedding=embedding)

        # Upsert into Qdrant
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            collection = os.getenv("QDRANT_COLLECTION", "startups")
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, check_compatibility=False)

            # ensure collection exists with correct vector size
            try:
                client.get_collection(collection_name=collection)
            except Exception:
                client.recreate_collection(collection_name=collection, vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE))

            point = rest_models.PointStruct(id=startup_id, vector=embedding, payload={"startup_id": startup_id, "name": name, "metadata": merged_metadata})
            client.upsert(collection_name=collection, points=[point])
        except Exception:
            # don't fail the whole task if qdrant is unavailable
            pass

        return {"status": "processed", "startup_id": startup_id}
    finally:
        db.close()


def scrape_and_process_yc(max_pages: int = 1):
    """Scrape YC companies, persist raw rows, then process each row."""
    db = SessionLocal()
    try:
        items = scrape_yc_companies(max_pages=max_pages)
        if not items:
            return {"status": "no_results", "count": 0}

        raw_ids = []
        for item in items:
            rec = persist_raw(
                db,
                source=item.get("source", "yc"),
                raw_text=item.get("description") or item.get("name") or "",
                metadata=item,
            )
            raw_ids.append(rec.id)
            process_raw(rec.id)

        return {"status": "scraped_and_processed", "count": len(raw_ids), "raw_ids": raw_ids}
    finally:
        db.close()


def reindex_all(collection: str = None):
    """Reindex all Startup rows into the configured Qdrant collection.

    This function is designed to be enqueued as an RQ background job.
    """
    db = SessionLocal()
    try:
        rows = db.query(Startup).all()
        if not rows:
            return {"status": "no_rows"}

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        coll = collection or os.getenv("QDRANT_COLLECTION", "startups")
        try:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, check_compatibility=False)
        except Exception as exc:
            payload = _qdrant_unavailable_error("connect", exc)
            payload["count"] = len(rows)
            return payload

        for s in rows:
            meta = s.meta or {}
            embedding = None
            if isinstance(meta, dict) and meta.get("embedding"):
                embedding = meta.get("embedding")
            else:
                text = " ".join(filter(None, [s.name or "", meta.get("description") or meta.get("tagline") or ""]))
                vecs = embed_texts([text])
                embedding = vecs[0].tolist()

            try:
                if not client.collection_exists(collection_name=coll):
                    client.create_collection(
                        collection_name=coll,
                        vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE),
                    )
            except Exception as exc:
                payload = _qdrant_unavailable_error("create_collection", exc)
                payload["count"] = len(rows)
                payload["collection"] = coll
                return payload

            point = rest_models.PointStruct(id=s.id, vector=embedding, payload={"startup_id": s.id, "name": s.name, "metadata": meta})
            try:
                client.upsert(collection_name=coll, points=[point])
            except Exception as exc:
                payload = _qdrant_unavailable_error("upsert", exc)
                payload["count"] = len(rows)
                payload["collection"] = coll
                return payload

        return {"status": "reindexed", "count": len(rows)}
    finally:
        db.close()
