# interfaces/tools/search_law.py
"""
Sprint 57 — SearchLawTool.
Leitar í igc_law_pilot Qdrant RAG collection.
Byggir á _rag_retrieve() í chat_routes.py.
"""
import logging
import os
from interfaces.tools.base import BaseTool

logger = logging.getLogger("alvitur.web")

_QDRANT_PATH = os.environ.get("QDRANT_LOCAL_PATH", "/workspace/Sigvaldi-/data/qdrant_laws_v2")
_RAG_COLLECTION = "alvitur_laws_v2"
_RAG_TOP_K = 3
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

            model = SentenceTransformer("intfloat/multilingual-e5-large")
            vector = model.encode([query], convert_to_numpy=True)[0]

            client = QdrantClient(path=_QDRANT_PATH)
            cols = [c.name for c in client.get_collections().collections]
            if _RAG_COLLECTION not in cols:
                logger.warning("[ALVITUR] SearchLawTool: collection %s ekki til", _RAG_COLLECTION)
                return []

            results = client.query_points(
                collection_name=_RAG_COLLECTION,
                query=vector.tolist(),
                limit=_RAG_TOP_K,
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
            logger.info("[ALVITUR] search_law hits=%d query=%r org_id=%s", len(hits), query[:60], org_id)
            return hits
        except Exception as e:
            logger.warning("[ALVITUR] search_law villa (graceful degradation): %s", e)
            return []
