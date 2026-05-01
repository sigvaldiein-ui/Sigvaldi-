"""Sprint 69 — SearchLawTool v2. Tengist alvitur_laws_v1 Qdrant collection."""
import logging, os
from interfaces.tools.base import BaseTool

logger = logging.getLogger("alvitur.web")
_QDRANT_PATH = os.environ.get("QDRANT_LOCAL_PATH", "/workspace/Sigvaldi-/data/qdrant_store")
_RAG_COLLECTION = "alvitur_laws_v1"
_RAG_TOP_K = 3
_RAG_SCORE_THRESHOLD = 0.40


class SearchLawTool(BaseTool):
    """Leitar í íslenskum lögum (alvitur_laws_v1)."""

    @property
    def name(self) -> str:
        return "search_law"

    @property
    def description(self) -> str:
        return (
            "Leitar í gagnagrunni íslenskra laga. "
            "Skilar viðeigandi lagagreinum með tilvísun og texta. "
            "Nota þegar notandi spyr um íslensk lög eða reglugerðir."
        )

    async def run(self, query: str = "") -> list:
        if not query:
            return []
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("intfloat/multilingual-e5-large")
            vector = model.encode([query], normalize_embeddings=True)[0]
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
                p = h.payload
                grein = p.get("grein", "")
                suffix = p.get("grein_suffix") or ""
                mgr = p.get("malsgrein") or ""
                law_nr = p.get("law_nr", "")
                law_year = p.get("law_year", "")
                law_title = p.get("law_title", "")
                gr_str = str(grein) + ". gr."
                if suffix:
                    gr_str += " " + str(suffix)
                if mgr:
                    gr_str = str(mgr) + ". mgr. " + gr_str
                title = gr_str + " laga nr. " + str(law_nr) + "/" + str(law_year) + " " + str(law_title)
                hits.append({
                    "text": p.get("text", ""),
                    "title": title.strip(),
                    "source": p.get("source_url", ""),
                    "law_nr": law_nr,
                    "law_year": law_year,
                    "grein": grein,
                    "domain": "legal",
                    "score": round(h.score, 4),
                })
            logger.info("[ALVITUR] search_law hits=%d query=%r", len(hits), query[:60])
            return hits
        except Exception as e:
            logger.warning("[ALVITUR] search_law villa (graceful degradation): %s", e)
            return []
