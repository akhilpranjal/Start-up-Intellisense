import numpy as np

_MODEL = None


def get_model(name: str = "all-MiniLM-L6-v2"):
    global _MODEL
    if _MODEL is None:
        # Lazy import keeps API startup fast; model loads on first embed call.
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(name)
    return _MODEL


def embed_texts(texts):
    model = get_model()
    vecs = model.encode(texts, show_progress_bar=False)
    return np.array(vecs)
