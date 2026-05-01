"""Sprint 70 — Singleton embedding model fyrir RAG+.

Lazy load a fyrsta call. CPU device.
Avoids 12s reload per request.
"""
from __future__ import annotations
import logging
import threading
from typing import List

log = logging.getLogger("alvitur.embeddings")
_lock = threading.Lock()
_model = None
_MODEL_NAME = "intfloat/multilingual-e5-large"


def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                log.info("[EMB] Loading %s...", _MODEL_NAME)
                _model = SentenceTransformer(_MODEL_NAME, device="cpu")
                log.info("[EMB] Model loaded, dim=%d", _model.get_embedding_dimension())
    return _model


def embed(text: str) -> List[float]:
    m = get_model()
    return m.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    m = get_model()
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        vecs = m.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_vecs.extend(vecs.tolist())
    return all_vecs
