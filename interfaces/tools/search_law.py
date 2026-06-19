# interfaces/tools/search_law.py
"""
Sprint 57 — SearchLawTool.
Leitar í igc_law_pilot Qdrant RAG collection.
Byggir á _rag_retrieve() í chat_routes.py.
"""
import logging
import os
from FlagEmbedding import FlagReranker
from interfaces.tools.base import BaseTool

logger = logging.getLogger("alvitur.web")

_QDRANT_PATH = os.environ.get("QDRANT_LOCAL_PATH", "/workspace/Sigvaldi-/data/qdrant_laws_v2")
_RAG_COLLECTION = "alvitur_laws_v2"
_RAG_TOP_K = 10
_RERANK_POOL = 40
_RAG_SCORE_THRESHOLD = 0.40



def secure_qdrant_query(org_id: str, query_vector, client, collection_name: str, limit: int = 5):
    """Sprint 99: Multi-tenant Qdrant query með org_id filter."""
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=Filter(must=[FieldCondition(key="org_id", match=MatchValue(value=org_id))]),
            limit=limit
        )
        return results
    except Exception:
        return client.search(collection_name=collection_name, query_vector=query_vector, limit=limit)


# Sprint 103 latency fix: embeddari er geymdur milli kalla
_EMBEDDING_MODEL = None
_RERANKER_MODEL = None  # Singleton: FlagReranker hlaðið einu sinni

def _get_embedding_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBEDDING_MODEL = SentenceTransformer('intfloat/multilingual-e5-large', device='cpu')
    return _EMBEDDING_MODEL

class SearchLawTool(BaseTool):
    """Leitar í íslenskum lögum og þingskjölum (igc_law_pilot)."""

    @property
    def name(self) -> str:
        return "search_law"

    @property
    def description(self) -> str:
        return (
            "Leitar í gagnagrunni íslenskra laga og þingskjala. "
            "Skilar þremur viðeigandi textabrotum með score, titli og slóð. "
            "Nota þegar notandi spyr um íslensk lög, reglugerðir eða þingmál."
        )

    async def run(self, query: str = "", org_id: str = "default", **kwargs) -> list[dict]:
        """
        Leitar í alvitur_laws_v2 (íslenskur opinber Lagasafn corpus).
        
        Args:
          query: leitarstrengur
          org_id: notandi org context (skráð til audit, EKKI notuð til filtering 
                  á public Lagasafn — multi-tenant isolation á við um user-uploads 
                  í aðskildum collections, ekki opinberan corpus)
          **kwargs: any future params, ignored (defensive)
        
        Skilar: listi af dicts [{text, title, source, date, score}]
        """
        if not query:
            return []
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer

            model = _get_embedding_model()
            vector = model.encode(["query: " + query], convert_to_numpy=True)[0]

            client = QdrantClient(host="127.0.0.1", port=6333)
            cols = [c.name for c in client.get_collections().collections]
            if _RAG_COLLECTION not in cols:
                logger.warning("[ALVITUR] SearchLawTool: collection %s ekki til", _RAG_COLLECTION)
                return []

            results = client.query_points(
                collection_name=_RAG_COLLECTION,
                query=vector.tolist(),
                limit=_RERANK_POOL,
            )
            hits = []
            for h in results.points:
                if h.score < _RAG_SCORE_THRESHOLD:
                    continue
                hits.append({
                    "text": h.payload.get("text", ""),
                    "title": h.payload.get("title", ""),
                    "source": h.payload.get("source", ""),
                    "date": h.payload.get("date", ""),
                    "domain": h.payload.get("domain", ""),
                    "score": round(h.score, 4),
                })
            # Reranker (ÓVIRKT): endurraða niðurstöðum með bge-reranker-v2-m3
            # Reranker slökktur skv. Opus 4.8 — embedding-eingöngu gefur betri röðun fyrir lögfræði
            global _RERANKER_MODEL
            if False:  # reranker slökktur
                try:
                    if _RERANKER_MODEL is None:
                        _RERANKER_MODEL = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
                    _pairs = [(query, h.get('text', '')) for h in hits]
                    _scores = _RERANKER_MODEL.compute_score(_pairs, normalize=True)
                    _ranked = sorted(zip(hits, _scores), key=lambda x: -x[1])
                    hits = [h for h, _ in _ranked]
                except Exception as _e:
                    logger.warning("[ALVITUR] reranker fellur til baka: %s", _e)
            logger.info("[ALVITUR] search_law hits=%d query=%r org_id=%s", len(hits[:10]), query[:60], org_id)
            # Dedup eftir titli (Sprint 90: fjarlægja tvítekningar)
            seen = set()
            deduped = []
            for h in hits:
                t = h.get('title', '')
                if t not in seen:
                    seen.add(t)
                    deduped.append(h)
            hits = deduped
            return hits[:5]
        except Exception as e:
            logger.warning("[ALVITUR] search_law villa (graceful degradation): %s", e)
            return []
