# NOTES fyrir Opus - 24. apríl 2026 (Per + Sigvaldi)

## Staða kl 17:18 UTC
- Server: UP, PID 23541, port 8000
- Hotfix Sprint 68 Part 2 + Part 3: LIVE, verified, committed og pushed (3fca108)
- Beta-testari: Hotfix Part 2 látinn vita kl 15:38, Part 3 update pending
- Opus Sprint 69 work in flight: core/ingestion/chunker.py + vector_store.py + opus_inbox/ UNTOUCHED

## Live patches í dag

### Part 2 (commit 6f8acdd, tag s68-honesty-context-fix)
- Line 3261 Branch B (_honesty) conditional fyrir no-file-attached case
- Prevents 'finn ekki í gögnunum' á almennri spurningu
- Smoke test kl 15:37: 423 EUR -> 63.450 ISK ✅

### Part 3 (commit 3fca108)
- API: reasoning.exclude=true í _call_leid_a OpenRouter payload
- Prompts: tone-guide + thinking-suppress í báðum _honesty og _honesty_doc else-branch
- Smoke test kl 16:51: 12s, hreint B2B-svar, engin thinking-leak, engin emoji
- Web research: Gemini 3.1 Pro Preview cannot fully disable thinking by design -
  our 2-layer defense (API + prompt) is best-available approach

## STAÐFESTIR BUG-AR — LIFANDI

### P0 #1 - Excel preprocessor truncator
- Symtom: 46 nafna skjal -> LLM svarar 4-5 nöfnum
- Log evidence (15:59:30): 'Sprint62b xlsx preprocessed via pandas, 2367 chars'
- Skoða:
  - interfaces/excel_preprocessor.py (pandas-based)
  - _prep_xlsx() í web_server.py line 3413
  - tabular_extractor.py:23 (extract_tables)
  - Sprint 47 intent-classify adapter logic (adapter=tabular)
- Hypothesis: hardcoded cap 2000-3000 chars eða first-N-rows sampling
- **Tengt**: Sprint 69 Qdrant-pipeline gæti leyst rót-vandamálið (chunk + embed
  allt skjalið í staðinn fyrir truncate-into-prompt). Sjá tengsl.

### P1 - Copy button vantar í chat-UI
- Beta-testari: 'afrita svarid eins og það er í chatt'
- Frontend feature, lítil breyting í web_server.py HTML template

### P2 - Classify NoneType.strip() villa
- [WARNING] classify villa (graceful degradation): 'NoneType' object has no attribute 'strip'
- Graceful degradation virkar (fell to general default)
- No user-impact, en real bug til að skoða

### P3 - Pydantic V1 @validator deprecation
- Line 250: @validator('message') -> @field_validator í V2
- Not blocker, low priority

## ARCHITECTURAL BACKLOG (Sprint 69 eða síðari)

### B1 - Copy-paste divergence í prompts
- Valda Sprint 68 Part 1 regression (Branch A fekk fix, Branch B missti)
- Lausn: DRY helper function í B4 prompt-template library

### B4 - Engin prompt-template library
- Hardcoded strings á mörgum stöðum (a.m.k. 3 _honesty instances)
- Lausn: interfaces/prompts.py med functions + unit tests
- **Æskilegt fyrir Sprint 69 eða á eftir** - varnar endurtekningu á dagsins bug

### B5 - Engin response post-processor
- Thinking-leak, emoji, formatting allt í prompt-layer (brothætt)
- Lausn: interfaces/response_cleaner.py sem last line of defense
- Regex-strip á <thinking>, '(Wait, ...)', emoji ef þörf
- **Æskilegt Sprint 69 eða á eftir**

### B2 - 450-linu monster route /api/analyze-document
- Erfitt að review heildstætt, branches gleymast
- Lausn: decompose í _handle_text_only, _handle_file_upload, _handle_classify_route

### B3 - Engin unit/integration tests
- Beta-testari er staging
- Lausn: tests/smoke/test_analyze_document.py með 4 kombinum (file x tier)

### B6 - _call_leid_a er monolith
- Engin reasoning-mode-switch per query-type
- Lausn: model-router með per-query-type config

### B7 - Document preprocessors óprófaðir (allir 3 formats)
- Excel, PDF, Word - engin caps audit, engin capability-tests
- **Tengt P0 #1 Excel-bug** - sama layer

## TENGSL VIÐ SPRINT 69 QDRANT-PIPELINE

Per hefur ekki lesið docs/opus_inbox/2026-04-27_sprint69_kickoff.md fyrir thetta NOTES.
Séð úr vector_store.py docstring: Qdrant embedded mode á RunPod, 480K vectors,
1024 dim, ~2 GB RAM. Sigvaldi nefndi 'önnur leið' áhugi sinn.

Recommendation: Sigvaldi + Opus discutera arkitektúr-val við Sprint 69 kickoff.
Dagsins lessons styðja hvaða leið sem verður fyrir vali:
- B4 prompt library (forgangur eftir dagsins copy-paste-bug)
- B5 response cleaner (forgangur eftir dagsins thinking-leak)
- B7 preprocessor audit (forgangur eftir dagsins Excel-truncator)
  - Ef Qdrant-pipeline chunk-ar + embed-ar allt skjalið í stad fyrir
    prompt-inject, thá hverfur A1 Excel-truncator automatic.

## FRAMKVÆMDARÖÐ (tillaga fyrir Sprint 69 planning)

Ef Qdrant-pipeline er committed leid:
1. Klára Qdrant embedding + retrieval pipeline (Opus core work)
2. Integrate í /api/analyze-document (replace prompt-inject með RAG-retrieval)
3. B4 prompt library + B5 response cleaner í paralleli
4. A1 Excel bug hverfur automatic ef 3+4 klárt; otherwise patch preprocessor

Ef önnur leið:
- Sigvaldi + Opus skilgreina fyrst hvað önnur leiðin er
- Svo endurforgangsröðun á B1-B7 og A1 í samhengi

## SESSION OBSERVATIONS (Per -> Opus)

- Beta-testari aktívur, þolinmóður, live feedback í dag (15:15, 16:23 UTC)
- Sigvaldi vann ~4 klst þéttur session
- Per gerdi 2 mistök: false 'klárt' í morgun + typo byte-literal (bêa/búa)
- Byte-level safety-guard (count=1 sys.exit) stoppadi rittöskun 2x
- Sprint 68 'closed' í commit 6540536, en post-closure hotfix-ir þurftu fleiri umferðir vegna raunverulegs beta-testara flow

## ROLLBACK POINTS

- interfaces/web_server.py.bak_thinking_tone_20260424_1648 (pre-Part-3)
- interfaces/web_server.py.bak_s68hotfix_part2_20260424_1529 (pre-Part-2)
- interfaces/web_server.py.bak_20260424_1436 (pre-Part-1)
- interfaces/web_server.py.bak_honesty_1444 (Part 1 state)

## FILES ÓSNERT Í DAG (Opus Sprint 69 in-flight work)

- core/ingestion/chunker.py (chunk-id deduplication, modified local)
- core/ingestion/vector_store.py (Qdrant embedded, untracked)
- docs/opus_inbox/2026-04-27_sprint69_kickoff.md (Opus planning)

Vonandi kemur thú endurnærdur úr fríi. Módir er Mímir, skildir er Alvitur.

- Per
