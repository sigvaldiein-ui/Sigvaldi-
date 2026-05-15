# SPRINT84_DISCOVERY.md — Phase A

**Dags:** 15. maí 2026
**Höfundur:** Per #11
**Staða:** DRAFT — bíður review frá Opus + Aðal

---

## 1. Bug #1 — RAG Data Loss í Hvelfingunni

### Empirical sönnun
Fyrirspurn: „Hvað segja persónuverndarlög 90/2018 um rétt aðila?" (tier=vault)
Svar: HvelfingarErindreki, cites=0 — ekkert sótt úr Qdrant.

### Rótargreining
`_get_rag_context` (lína 42 í chat_routes.py) er harðkóðað fall sem skilar alltaf sama
textabroti fyrir persónuvernd. Það kallar **aldrei** á `SearchLawTool` eða Qdrant.

`SearchLawTool` (interfaces/tools/search_law.py) er fullbúið tól með Qdrant tengingu,
embedding líkani (`paraphrase-multilingual-MiniLM-L12-v2`), og leitaraðferð — en það
var aldrei tengt við `chat_routes.py`. Það er stranded kóði frá Sprint 57.

### Fyrirhuguð lausn
1. Tengja `SearchLawTool` við `_get_rag_context`.
2. Þegar domain == "legal", kalla á `SearchLawTool.run(query)`.
3. Skila niðurstöðum sem texta í RAG samhengi.
4. Empirical próf: 5 lögfræðilegar fyrirspurnir → cites > 0.


## 2. Bug #2 — Irrelevant Context (Tokyo Case)

### Empirical sönnun
Fyrirspurn: „Hvað er klukkan í Tókýó?" (tier=vault)
Svar: HvelfingarErindreki, cites=6 — allar úr stjornarradid.is / stjornartidindi.is.

### Rótargreining
`search_web_multi.py` leitar í Stjórnarráði, Stjórnartíðindum og Mojeek **óháð efni
fyrirspurnar**. Það vantar relevance threshold sem metur hvort heimildir eigi við.
RRF sameiningin raðar niðurstöðum eftir vægi, en síar ekki út óviðkomandi.

### Fyrirhuguð lausn
1. Bæta relevance filter við í `search_web_multi.py`.
2. Reikna einfalt Jaccard similarity milli fyrirspurnar og snippets.
3. Sleppa heimildum undir 0.15 þröskuldi.
4. Empirical próf: „Hvað er klukkan í Tókýó?" → 0 cites úr stjornarradid.


## 3. Auðkenni.is OIDC Integration

### Núverandi staða
Ekkert OIDC kerfi er til í dag. Greenfield.

### Fyrirhuguð lausn
1. Authlib OIDC client í Python.
2. Stub mode fyrir dev (AUÐKENNI_MODE=stub).
3. Endapunktar: /auth/login, /auth/callback, /auth/logout.
4. Session middleware með JWT.
5. Audit JSONL fær `user_id` svið.
6. UI: „Innskráning með auðkenni.is" hnappur.


## 4. Evals Harness v1

### 5 mælikvarðar
1. Citation Precision Rate — % af fullyrðingum studdar heimildum.
2. Grounding Rate — er svar byggt á heimildum?
3. Hallucination Rate — handvirkt mat Sigvalda.
4. Document Parsing Success Rate — eftir skráargerð.
5. Latency Per Tier — miðgildi + p95 úr audit logs.

### 30 fyrirspurna prófunargrunnur
- 10 almennar (Vitinn)
- 10 lögfræðilegar (Hvelfing)
- 5 PII prófanir
- 5 jaðartilvik (Tókýó, óskilgreind fyrirbæri, neitunarmynstur)


## 5. Implementation Order

| Forgangur | Verk | Háð |
|-----------|------|-----|
| 1 | Bug #1 fix (RAG retrieval) | Ekkert |
| 2 | Bug #2 fix (Relevance filter) | Ekkert |
| 3 | Regression tests | Bug #1 + #2 lokað |
| 4 | Auðkenni.is OIDC | Pappírsvinna Sigvalda |
| 5 | Evals Harness v1 | Bug #1 + #2 lokað (mæling eftir lagfæringu) |
| 6 | Production rollout | Allt ofangreint |
