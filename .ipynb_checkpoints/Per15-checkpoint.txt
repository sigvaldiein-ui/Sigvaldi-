# Sprint 80c v2 — Multi-Source Web Search Strategy

**Date:** 10. mai 2026
**Status:** Phase B — Strategy (Gate B pending Opus review)
**Author:** Per (Executor), Sigvaldi (HITL), with Opus QA

---

## 1. Empirically Grounded Sources (Phase A confirmed)

| # | Source | Endpoint | Type | Compliance |
|---|--------|----------|------|------------|
| 1 | stjornarradid.is | /rikisstjorn/skipan-rikisstjornar/ | HTML (Eplica CMS) | Public gov |
| 2 | stjornartidindi.is | /api/v1/rss/a-deild | RSS XML | Public RSS |
| 3 | althingi.is | www.althingi.is | HTML (Eplica CMS) | search=yes, ai-train=no |
| 4 | Wayback CDX | web.archive.org/cdx/ | JSON API | Public archive |
| 5 | Mojeek API | api.mojeek.com/search | JSON API | DPA committed |

## 2. RRF Merger Formula (Reciprocal Rank Fusion)

score(d) = sum( 1 / (k + rank_i) ) for k = 60

Example: Document ranked #1 in one source and #3 in another:
score = 1/(60+1) + 1/(60+3) = 0.01639 + 0.01587 = 0.03226

## 3. Citation Schema (with source_api)

{
  "title": "Document title",
  "url": "https://...",
  "snippet": "Short description",
  "source_api": "stjornarradid|stjornartidindi|althingi|wayback|mojeek",
  "rank": 1,
  "score": 0.032,
  "accessed_at": "2026-05-10T12:00:00Z"
}

## 4. Source Weighting

| Source | Weight | Rationale |
|--------|--------|-----------|
| stjornarradid.is | 2.0x | Official government (authoritative) |
| stjornartidindi.is | 2.0x | Official legal gazette |
| althingi.is | 1.5x | Parliamentary documents |
| Mojeek API | 1.0x | General web search |
| Wayback CDX | 0.8x | Historical archive |

## 5. Fetcher Pattern (per source)

async def fetch(query: str, max_results: int = 5) -> dict:
    Returns {"citations": [...], "source": "name", "raw_count": N}

## 6. Orchestrator Pattern

All fetchers called in parallel with asyncio.gather() and results merged via RRF.

## 7. Empirical Test Cases (Phase D)

| # | Query | Expected winner | Gate |
|---|-------|-----------------|------|
| 1 | "Who is the Prime Minister of Iceland in May 2026?" | stjornarradid.is | Response includes current PM |
| 2 | "Personal Data Protection Act 90/2018" | stjornartidindi.is + Mojeek | Citations from >=2 sources |
| 3 | "History of Althingi" | Wayback + Mojeek | Wayback citation appears |
| 4 | "Latest laws from Althingi" | stjornartidindi.is | RSS entry appears |
| 5 | "Financial Supervisory Authority" | Mojeek + stjornarradid.is | Mix of gov and web |

## 8. Heuristic Compliance

| # | Heuristic | How |
|---|-----------|-----|
| 1 | Empirical-first | All sources confirmed in Phase A |
| 2 | No SPoF | 5 independent sources with RRF merger |
| 3 | Trust > Capability | Citation schema with source_api + timestamp |
| 4 | Execution-verification | Each fetcher tested standalone before integration |