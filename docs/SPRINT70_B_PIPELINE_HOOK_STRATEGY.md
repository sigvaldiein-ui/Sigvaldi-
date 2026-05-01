# Sprint 70 Track B — RAG+ Pipeline Hook Strategy
# Date: 2026-04-25 | Author: Sonnet 4.6
# Status: DRAFT — awaiting Opus GREEN

---

## Section 1: Trigger Logic

Primary trigger: intent_classify(query).domain == "legal"

Secondary trigger (keyword fallback):
  Pattern: re.search(r'\d+/\d{4}|gr\.|mgr\.|tölul\.|lög\s+nr\.', query, re.IGNORECASE)
  Rationale: User may ask "hvað segir 36. gr. um fasteignalán" — classify may return
  "financial" due to keywords, but RAG should still fire.

Trigger taxonomy:
  TRIGGER_PRIMARY:   domain == "legal" (from intent classifier)
  TRIGGER_SECONDARY: keyword pattern match in query
  TRIGGER_NONE:      neither — skip retrieval

Edge case — Excel + legal query:
  Intent domain may be "financial" (Excel adapter) but query contains legal keywords.
  Decision: Run BOTH financial processing AND legal retrieval.
  Combine: Excel analysis in main response + legal citations in footer.
  Rationale: User asking "er þetta í samræmi við 36. gr. fasteignalánalaga?" with
  Excel file needs BOTH the data analysis AND the law.

---

## Section 2: Retrieval Configuration

top_k: 3 (default). Adaptive: if top score < 0.60, expand to 5.
  Rationale: Low confidence on top hit means corpus may have relevant chunks further down.

score_threshold: 0.40
  Below threshold: no retrieval — return refusal message (see Section 4)
  0.40-0.60: retrieve with low_confidence flag in payload
  0.60+: full confidence retrieval

chunk hydration:
  Return: chunk text + citation + source_url
  Do NOT return parent grein context automatically — too much tokens.
  Exception: if chunk is malsgrein (chunk_level=="malsgrein"), also fetch parent grein.
  Rationale: Malsgrein without parent loses legal context.

multi-query:
  If domain=="legal" AND query contains multiple law references (2+ lögnúmer patterns):
    Run retrieval per detected law_nr, merge results, deduplicate by chunk_id.
  Otherwise: single query.

---

## Section 3: Prompt Injection Format

Injected AFTER existing system prompt, BEFORE user message:

---
HEIMILDIR ÚR ÍSLENSKUM LÖGUM (RAG+):

[1] {citation_1}
{text_1}
Heimild: {source_url_1}

[2] {citation_2}
{text_2}
Heimild: {source_url_2}

[3] {citation_3}
{text_3}
Heimild: {source_url_3}

LEIÐBEININGAR:
- Svaraðu EINGÖNGU út frá ofangreindum lagatextum þegar þeir eiga við.
- Vitnaðu í þá með kanonískri tilvísun: "X. tölul. Y. mgr. Z. gr. laga nr. NNNN/ÁÁÁÁ".
- Ef spurningin er ekki svarleg úr þessum textum, segðu það beint.
- Blandaðu ekki saman lagatilvísunum og almennri þekkingu án skýrs aðskilnaðar.
---

Interaction with thinking-suppress hammer (Sprint 68 Part 3):
  /no_think prefix MUST remain on classify calls — RAG injection does NOT affect this.
  RAG injection goes into system prompt context, not into the classify prompt.
  No conflict.

---

## Section 4: Refusal Behavior

Case A — No chunks above threshold (empty retrieval):
  Response: "Finn ekki viðeigandi lagatexta í gagnagrunni Alvitur fyrir þessa fyrirspurn.
  Gagngrunnurinn inniheldur 4 lög (145/1994, 90/2003, 118/2016, 90/2018).
  Ef spurningin varðar önnur lög, hefur corpus ekki verið uppfærður."
  Do NOT fallback to Gemini general knowledge for legal queries.
  Rationale: Hallucinated law is worse than honest "don't know".

Case B — Low score chunks (0.40-0.60):
  Include chunks but add caveat in prompt injection:
  "ATHUGIÐ: Eftirfarandi heimildir hafa lágt samsvörunargildi ({score:.2f}).
  Notaðu með varúð."

Case C — Query outside corpus (e.g. lög nr. 50/2012):
  Detected by: zero hits OR all hits from wrong law_nr.
  Response: "Lög nr. 50/2012 eru ekki í gagnagrunni Alvitur. Corpus nær til:
  laga nr. 145/1994, 90/2003, 118/2016 og 90/2018."

---

## Section 5: Pipeline Integration Points

TWO integration points exist:
  (a) interfaces/web_server.py — /api/analyze-document (Leið A + B)
  (b) interfaces/chat_routes.py — /api/chat (vault tier)

Recommendation: core/rag_orchestrator.py::retrieve_legal_context(query, intent)
  Single function, called by both routes. DRY pattern.

Function signature:
  async def retrieve_legal_context(
      query: str,
      intent_domain: str,
      top_k: int = 3,
  ) -> dict:
      # Returns: {chunks: List[dict], used: bool, latency_ms: int, top_score: float}

Calling pattern in web_server.py:
  BEFORE LLM call:
    rag_result = await retrieve_legal_context(query, intent.domain)
    if rag_result["used"]:
        system_prompt += build_rag_injection(rag_result["chunks"])

Calling pattern in chat_routes.py:
  Same pattern — vault tier also benefits from legal grounding.

---

## Section 6: Observability + Telemetry

Log prefix: [RAG] — grep-able in web_server.log

Log fields per retrieval:
  query_snippet: query[:60]  (truncated for privacy)
  intent_domain: str
  trigger_type: "primary" | "secondary" | "none"
  top_k_chunks: [chunk_id_1, chunk_id_2, ...]
  top_score: float
  retrieval_used: bool
  latency_ms: {embedding: int, search: int, total: int}

Example log line:
  [RAG] domain=legal trigger=primary top_score=0.892 chunks=3
        ids=[118_2016_g20,118_2016_g7,118_2016_g49] latency_ms=285 used=True

Metrics to track weekly:
  - retrieval_used rate (% of legal queries that get RAG)
  - avg top_score (quality signal)
  - zero_hit rate (corpus gap signal)

---

## Open Questions for Opus

Q1: Fallback til Gemini general knowledge ef zero hits?
  Mín tillaga: NEI fyrir legal queries (hallucination risk of fake laws).
  En hvað ef user er að spyrja um löglegt hugtak, ekki tiltekna grein?
  Dæmi: "hvað þýðir greiðslumat?" — þarf ekki RAG, þarf skilgreiningu.

Q2: Embedding á query — sama model og corpus (e5-large)?
  e5-large er 12s load time. Í production með mörgum samtímis requests þarf
  persistent model í memory. Hvernig stjórnum við þessu (singleton vs reload)?

Q3: Chunk hydration fyrir malsgrein — sækja parent automatiskt?
  Ef chunk er "2. mgr. 36. gr." — á við alltaf sækja "36. gr." heildina?
  Gæti verið of mikið tokens ef grein er löng (>400 tokens = sub-split threshold).

Q4: Multi-tenant scope — tenant_id="system" vs tenant_id="user_XXX"?
  Alvitur_laws_v1 er system corpus. Þegar við bætum við user-uploaded skjölum
  (Sprint 75+) þurfum við separation. Á við setja tenant_id í payload núna
  (forward-compatible) eða seinna?

Q5: Latency budget — 285ms embedding er 25% af 1.1s typical LLM latency.
  Ásættanlegt? Eða á við pre-embed common queries (cache)?

---

## Opus 4.7 Answers (2026-04-25)

Q1 FALLBACK POLICY (dual-policy):
  vault tier: refuses cleanly — "Finn ekki viðeigandi lagatexta í corpus Alvitur."
  general tier: falls to Gemini með caveat flag in response.
  Vault loforð er non-negotiable — aldrei Gemini general knowledge á vault tier.

Q2 SINGLETON (lazy load):
  JA. core/embeddings.py, lazy load a fyrsta call, CPU device.
  Avoids 12s reload per request.

Q3 PARENT HYDRATION:
  JA med caveat: ef malsgrein sub-chunk og parent grein <600 tokens → hydrate.
  Ef parent >=600 tokens → skip (forðast context overflow).

Q4 TENANT_ID — NUNA (ekki Sprint 75):
  Bæta tenant_id="system" i payload schema OG retrieval filter.
  Sprint 72 ephemeral vault krefst þessa. P0 fyrir Sprint 70.

Q5 EMBEDDING CACHE — EKKI NUNA:
  285ms er <5% heildartíma. Cache hit rate <5%.
  Ef p95 fer yfir 500ms → GPU offload, ekki cache.
