"""Reindex all `Startup` rows into Qdrant.

Usage:
    python scripts/reindex_qdrant.py

Requires Qdrant to be reachable via `QDRANT_URL` (default http://localhost:6333).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import SessionLocal
from app.models import Startup
from embeddings.local_embedder import embed_texts
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from qdrant_client.http.models import VectorParams, Distance
import os


def reindex(collection: str = "startups"):
    db = SessionLocal()
    try:
        rows = db.query(Startup).all()
        if not rows:
            print("No startups found in DB to index.")
            return

        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        try:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, check_compatibility=False)
        except Exception as exc:
            print(f"Qdrant unavailable during connect: {exc}")
            return

        for s in rows:
            meta = s.meta or {}
            # reuse stored embedding if available
            embedding = None
            if isinstance(meta, dict) and meta.get("embedding"):
                embedding = meta.get("embedding")
            else:
                # construct a text for embedding
                text = " ".join(filter(None, [s.name or "", meta.get("description") or meta.get("tagline") or ""]))
                vecs = embed_texts([text])
                embedding = vecs[0].tolist()

            # ensure collection exists
            try:
                if not client.collection_exists(collection_name=collection):
                    client.create_collection(
                        collection_name=collection,
                        vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE),
                    )
            except Exception as exc:
                print(f"Qdrant unavailable during create_collection for {collection}: {exc}")
                return

            point = rest_models.PointStruct(id=s.id, vector=embedding, payload={"startup_id": s.id, "name": s.name, "metadata": meta})
            try:
                client.upsert(collection_name=collection, points=[point])
            except Exception as exc:
                print(f"Qdrant unavailable during upsert for {collection}: {exc}")
                return
            print(f"Upserted startup {s.id} -> {s.name}")
    finally:
        db.close()


if __name__ == "__main__":
    coll = os.getenv("QDRANT_COLLECTION", "startups")
    reindex(collection=coll)
