from fastapi import FastAPI
from pydantic import BaseModel
import os

from . import db

app = FastAPI(title="Startup Intelligence Platform - API")


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


class SearchRequest(BaseModel):
    query: str


@app.post("/search")
def search(req: SearchRequest):
    # Placeholder: call embedder -> qdrant -> return results
    # For now return a static response
    return {"query": req.query, "results": []}


def start():
    import uvicorn

    uvicorn.run("app.api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
