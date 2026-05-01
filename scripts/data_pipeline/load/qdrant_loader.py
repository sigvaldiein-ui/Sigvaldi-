"""Hleður lagalegum chunks í Qdrant — server eða local mode (K3 Load)."""
import os
import re
import logging
from typing import Iterator, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("alvitur.qdrant_loader")

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_PATH = os.getenv("QDRANT_PATH", "/workspace/Sigvaldi-/data/qdrant_laws_v2")
COLLECTION_NAME = os.getenv("QDRANT_LAWS_V2", "alvitur_laws_v2")
VECTOR_DIM = 1024  # multilingual-e5-large


def _get_client() -> QdrantClient:
    """Skilar Qdrant client — local mode ef server ekki til."""
    if QDRANT_URL:
        logger.info(f"Tengi við Qdrant server: {QDRANT_URL}")
        return QdrantClient(url=QDRANT_URL)
    else:
        logger.info(f"Qdrant local mode: {QDRANT_PATH}")
        return QdrantClient(path=QDRANT_PATH)


def _extract_citation_full(title: str, section: str) -> str:
    """Býr til canonical citation: '36. gr. laga nr. 118/2016 um fasteignalán'"""
    hlutar = []
    
    if section and section not in ("Óskipt", "Inngangur"):
        hlutar.append(section)
    
    nr_match = re.search(r"(?:nr\.|laga nr\.)\s*(\d+/\d{4})", title)
    if nr_match:
        hlutar.append(f"laga nr. {nr_match.group(1)}")
    
    clean_title = re.sub(r"\s+nr\.\s*$", "", title)
    clean_title = re.sub(r"\s*\d{4}\s+nr\.?\s*$", "", clean_title)
    if clean_title and len(clean_title) < 120:
        hlutar.append(clean_title)
    
    return " ".join(hlutar) if hlutar else title[:150]


def create_collection_if_missing(client: QdrantClient):
    """Býr til alvitur_laws_v2 án þess að snerta v1."""
    collections = [c.name for c in client.get_collections().collections]
    
    if COLLECTION_NAME in collections:
        info = client.get_collection(COLLECTION_NAME)
        points = info.points_count if info.points_count else 0
        logger.info(f"Collection '{COLLECTION_NAME}' til staðar — {points} points")
        return
    
    logger.info(f"Bý til nýtt collection: {COLLECTION_NAME} (dim={VECTOR_DIM})")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )
    logger.info("  Collection búið til")


def load_chunks_to_qdrant(
    chunks: Iterator[Dict[str, Any]],
    client: QdrantClient,
    batch_size: int = 50,
) -> int:
    """Vektorar og hleður chunks í Qdrant. Skilar fjölda punkta."""
    from core.embeddings import embed_batch
    
    total = 0
    batch_texts = []
    batch_meta = []
    
    for chunk in chunks:
        batch_texts.append(f"query: {chunk['text']}")
        batch_meta.append(chunk['metadata'])
        
        if len(batch_texts) >= batch_size:
            total = _upsert_batch(client, batch_texts, batch_meta, total)
            batch_texts = []
            batch_meta = []
    
    if batch_texts:
        total = _upsert_batch(client, batch_texts, batch_meta, total)
    
    logger.info(f"Alls hlaðið: {total} points í '{COLLECTION_NAME}'")
    return total


def _upsert_batch(client: QdrantClient, texts: list, metas: list, start_id: int) -> int:
    """Innfelldir og sendir einn batch."""
    from core.embeddings import embed_batch
    
    vectors = embed_batch(texts)
    points = []
    
    for i, vec in enumerate(vectors):
        meta = metas[i]
        citation = _extract_citation_full(meta["title"], meta["section"])
        points.append(PointStruct(
            id=start_id + i,
            vector=vec,
            payload={
                "text": texts[i].replace("query: ", ""),
                "title": meta["title"],
                "source": meta["source"],
                "section": meta["section"],
                "citation_full": citation,
            },
        ))
    
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"  Hleð: {start_id + len(points)} points...")
    return start_id + len(points)


# --- Smoke test ---
if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/workspace/Sigvaldi-")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    
    from scripts.data_pipeline.sources.igc_fetcher import fetch_igc_stream
    from scripts.data_pipeline.transform.igc_chunker import chunk_igc_document
    
    print("=== K3 Qdrant Loader Smoke Test ===\n")
    
    client = _get_client()
    create_collection_if_missing(client)
    
    print("\nSæki 5 lög úr IGC-2024...")
    docs = []
    for doc in fetch_igc_stream("law_law", limit=None):
        docs.append(doc)
    
    print(f"Chunkar...")
    all_chunks = []
    for doc in docs:
        for chunk in chunk_igc_document(doc["title"], doc["source"], doc["text"]):
            all_chunks.append(chunk)
    
    print(f"\n{len(all_chunks)} chunks tilbúnir")
    
    if all_chunks:
        from json import dumps
        chunk = all_chunks[0]
        citation = _extract_citation_full(chunk["metadata"]["title"], chunk["metadata"]["section"])
        sample = {
            "text": chunk["text"][:100] + "...",
            "title": chunk["metadata"]["title"],
            "section": chunk["metadata"]["section"],
            "source": chunk["metadata"]["source"],
            "citation_full": citation,
        }
        print("\nDæmi payload:")
        print(dumps(sample, indent=2, ensure_ascii=False))
    
    print(f"\nHleð {len(all_chunks)} chunks í '{COLLECTION_NAME}'...")
    total = load_chunks_to_qdrant(iter(all_chunks), client)
    
    print(f"\n=== Staðfest: {total} points í Qdrant ===")
    
    info = client.get_collection(COLLECTION_NAME)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Points: {info.points_count}")
    print(f"Staðsetning: {QDRANT_PATH}")
    
    print("\n Smoke test klárt!")
