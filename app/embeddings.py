from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Description:
Load the local sentence-transformer once per process.
Input Description:
No direct inputs.
Output Description:
Returns a cached SentenceTransformer instance.
"""
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Description:
Convert input text into a normalized embedding vector.
Input Description:
text is the string to embed.
Output Description:
Returns a list of float embedding values.
"""
    clean_text = (text or "").strip() or "empty"
    model = _get_model()
    vector = model.encode(clean_text, normalize_embeddings=True)
    return [float(value) for value in vector.tolist()]
