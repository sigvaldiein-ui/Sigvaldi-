"""Sprint 69 Track D — BaseVectorStore fyrir Qdrant embedded mode.

Memory note (Opus C.1 GREEN):
  Self-hosted Qdrant a RunPod, ekki Cloud.
  480K vectors x 1024 dim x float32 = ~2 GB RAM.
"""
from __future__ import annotations
import uuid
from dataclasses import asdict
from typing import List, Optional
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter, FieldCondition, MatchValue,
)
from sentence_transformers import SentenceTransformer

from core.ingestion.chunker import Chunk

log = logging.getLogger("vector_store")

COLLECTION_NAME = "alvitur_laws_v1"
VECTOR_DIM = 1024
QDRANT_PATH = "data/qdrant_store"


class LegalVectorStore:
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        qdrant_path: str = QDRANT_PATH,
        collection: str = COLLECTION_NAME,
    ):
        self.model = SentenceTransformer(model_name, device="cpu")
        self.client = QdrantClient(path=qdrant_path)
        self.collection = collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )
            log.info("Created collection: %s", self.collection)
        else:
            log.info("Collection exists: %s", self.collection)

    def _embed(self, text: str) -> List[float]:
        return self._embed_batch([text])[0]

    def _embed_batch(self, texts: List[str], batch_size: int = 64) -> list:
        all_vecs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            vecs = self.model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
            all_vecs.extend(vecs.tolist())
        return all_vecs

    def upsert_chunks(self, chunks: List[Chunk]) -> int:
        texts = [ch.text for ch in chunks]
        vecs = self._embed_batch(texts)
        points = []
        for ch, vec in zip(chunks, vecs):
            payload = asdict(ch)
            points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, ch.chunk_id)),
                vector=vec,
                payload=payload,
            ))
        self.client.upsert(collection_name=self.collection, points=points)
        log.info("Upserted %d chunks into %s", len(points), self.collection)
        return len(points)

    def search(
        self,
        query: str,
        top_k: int = 5,
        law_nr: Optional[int] = None,
        law_year: Optional[int] = None,
    ) -> list:
        vec = self._embed(query)
        filters = []
        if law_nr:
            filters.append(FieldCondition(key="law_nr", match=MatchValue(value=law_nr)))
        if law_year:
            filters.append(FieldCondition(key="law_year", match=MatchValue(value=law_year)))
        filt = Filter(must=filters) if filters else None
        from qdrant_client.models import QueryRequest
        results = self.client.query_points(
            collection_name=self.collection,
            query=vec,
            limit=top_k,
            query_filter=filt,
            with_payload=True,
        ).points
        return results

    def count(self) -> int:
        return self.client.count(collection_name=self.collection).count
