"""Sprint 70 Track C — RAG+ orchestrator.

Central retrieval logic for Alvitur.
Both /api/chat (vault) and /api/analyze-document (general) call into this.
DRY pattern: one place to update retrieval logic.
"""
from __future__ import annotations
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Literal, Optional

log = logging.getLogger("alvitur.rag")

# Module-level imports fyrir patching i tests
from core.embeddings import embed
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

_QDRANT_PATH = "data/qdrant_store"
_COLLECTION  = "alvitur_laws_v1"
_TOP_K_DEFAULT = 3
_TOP_K_EXPANDED = 5
_SCORE_HIGH = 0.60
_SCORE_LOW  = 0.40

_LEGAL_KEYWORDS = re.compile(
    r'\d+/\d{4}|gr\.|mgr\.|tölul\.|lög\s+nr\.|lögnúmer|lagagrein|fasteignal[aá]n|bókhald|persónuvernd|tekjuskattur|skattalög|reglugerð|lagaákvæð',
    re.IGNORECASE
)

CORPUS_LAWS = {
    (145, 1994): "lög um bókhald",
    (90, 2003):  "lög um tekjuskatt",
    (118, 2016): "lög um fasteignalán til neytenda",
    (90, 2018):  "lög um persónuvernd",
}


@dataclass
class RetrievalResult:
    chunks: List[dict] = field(default_factory=list)
    top_score: float = 0.0
    used_retrieval: bool = False
    fallback_to_gemini: bool = False
    refusal: Optional[str] = None
    trigger_type: str = "none"
    latency_ms: int = 0


def _trigger_type(intent_domain: str, query: str) -> str:
    if intent_domain == "legal":
        return "primary"
    if _LEGAL_KEYWORDS.search(query):
        return "secondary"
    return "none"


def _build_refusal(tier: str) -> str:
    corpus = ", ".join(f"lög nr. {nr}/{yr}" for (nr, yr) in CORPUS_LAWS)
    if tier == "vault":
        return (
            f"Finn ekki viðeigandi lagatexta í gagnagrunni Alvitur fyrir þessa fyrirspurn. "
            f"Corpus nær til: {corpus}."
        )
    return ""


def retrieve_legal_context(
    query: str,
    intent_domain: str,
    tier: Literal["general", "vault"] = "general",
    tenant_id: str = "system",
    top_k: int = _TOP_K_DEFAULT,
) -> RetrievalResult:
    t_start = time.time()
    trigger = _trigger_type(intent_domain, query)

    if trigger == "none":
        log.info("[RAG] domain=%s trigger=none — skip retrieval", intent_domain)
        return RetrievalResult(trigger_type="none")

    try:
        t_emb = time.time()
        vec = embed(query)
        emb_ms = int((time.time() - t_emb) * 1000)

        t_search = time.time()
        client = QdrantClient(path=_QDRANT_PATH)

        # tenant_id filter
        filt = Filter(must=[
            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
        ]) if tenant_id else None

        # Adaptive top_k
        results = client.query_points(
            collection_name=_COLLECTION,
            query=vec,
            limit=top_k,
            query_filter=filt,
            with_payload=True,
        ).points
        search_ms = int((time.time() - t_search) * 1000)

        # Ef top score laegt → expand
        if results and results[0].score < _SCORE_HIGH and top_k == _TOP_K_DEFAULT:
            results = client.query_points(
                collection_name=_COLLECTION,
                query=vec,
                limit=_TOP_K_EXPANDED,
                query_filter=filt,
                with_payload=True,
            ).points

        total_ms = int((time.time() - t_start) * 1000)

        # Filter under threshold
        above = [r for r in results if r.score >= _SCORE_LOW]
        top_score = above[0].score if above else 0.0

        log.info(
            "[RAG] domain=%s trigger=%s top_score=%.3f chunks=%d "
            "ids=%s latency_ms=%d(emb=%d,search=%d) used=%s",
            intent_domain, trigger, top_score, len(above),
            [r.payload.get("chunk_id","?") for r in above[:3]],
            total_ms, emb_ms, search_ms, bool(above)
        )

        if not above:
            refusal = _build_refusal(tier)
            fallback = tier == "general"
            return RetrievalResult(
                top_score=0.0,
                used_retrieval=False,
                fallback_to_gemini=fallback,
                refusal=refusal if tier == "vault" else None,
                trigger_type=trigger,
                latency_ms=total_ms,
            )

        # Hydrate chunks — parent hydration for malsgrein
        hydrated = []
        for r in above:
            p = r.payload
            chunk = {
                "chunk_id":   p.get("chunk_id",""),
                "text":       p.get("text",""),
                "grein":      p.get("grein",""),
                "grein_suffix": p.get("grein_suffix"),
                "malsgrein":  p.get("malsgrein"),
                "law_nr":     p.get("law_nr",""),
                "law_year":   p.get("law_year",""),
                "law_title":  p.get("law_title",""),
                "source_url": p.get("source_url",""),
                "score":      round(r.score, 4),
                "low_confidence": r.score < _SCORE_HIGH,
            }
            # Parent hydration for malsgrein
            if p.get("chunk_level") == "malsgrein" and p.get("parent_chunk_id"):
                parent = client.query_points(
                    collection_name=_COLLECTION,
                    query=vec,
                    limit=1,
                    query_filter=Filter(must=[
                        FieldCondition(key="chunk_id",
                                       match=MatchValue(value=p["parent_chunk_id"]))
                    ]),
                    with_payload=True,
                ).points
                if parent and parent[0].payload.get("token_count",999) < 600:
                    chunk["parent_text"] = parent[0].payload.get("text","")

            hydrated.append(chunk)

        return RetrievalResult(
            chunks=hydrated,
            top_score=top_score,
            used_retrieval=True,
            fallback_to_gemini=False,
            trigger_type=trigger,
            latency_ms=total_ms,
        )

    except Exception as e:
        log.warning("[RAG] villa (graceful degradation): %s", e)
        return RetrievalResult(trigger_type=trigger, latency_ms=0)


def build_rag_injection(chunks: List[dict]) -> str:
    if not chunks:
        return ""
    lines = ["\nHEIMILDIR ÚR ÍSLENSKUM LÖGUM (RAG+):\n"]
    for i, ch in enumerate(chunks, 1):
        grein = ch.get("grein","")
        suffix = ch.get("grein_suffix") or ""
        mgr = ch.get("malsgrein") or ""
        law_nr = ch.get("law_nr","")
        law_yr = ch.get("law_year","")
        law_title = ch.get("law_title","")
        gr_str = f"{grein}. gr." + (f" {suffix}" if suffix else "")
        if mgr:
            gr_str = f"{mgr}. mgr. " + gr_str
        citation = f"{gr_str} laga nr. {law_nr}/{law_yr} {law_title}".strip()
        caveat = " [lágt samsvörunargildi]" if ch.get("low_confidence") else ""
        lines.append(f"[{i}] {citation}{caveat}")
        if ch.get("parent_text"):
            lines.append(f"Samhengi (foreldri-grein): {ch['parent_text'][:300]}")
        lines.append(ch.get("text",""))
        lines.append(f"Heimild: {ch.get('source_url','')}\n")
    lines.append(
        "LEIÐBEININGAR:\n"
        "- Svaraðu EINGÖNGU út frá ofangreindum lagatextum þegar þeir eiga við.\n"
        "- Vitnaðu með kanonískri tilvísun: X. tölul. Y. mgr. Z. gr. laga nr. NNNN/ÁÁÁÁ.\n"
        "- Ef spurningin er ekki svarleg úr þessum textum, segðu það beint.\n"
    )
    return "\n".join(lines)
