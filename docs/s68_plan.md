# Sprint 68 — Plan (Opus-approved)

**Branch:** `sprint68-queue`
**Started:** 2026-04-23
**Strategy:** Sequential tracks with design-before-code gates.

## Tracks

### Track A — Depth Classifier Hardening
- A.1 Forensic analysis (GATE: Opus review before A.2)
- A.2 Rule redesign (keywords + precedence + word-count heuristic)
- A.3 Eval + commit (gates: depth_acc ≥ 0.80, standard F1 > 0.50, domain F1 held)
- Tag: `s68-a-depth-hardened`

### Track B — RAG+ Metadata Schema (starts only after A.3)
- B.1 Legal reference format workshop (GATE: Opus review before B.2)
- B.2 Pydantic schema (LegalReference + RagDocumentChunk)
- B.3 Unit tests (10+) + commit
- Tag: `s68-b-rag-schema`

### Track C — Vector Store Abstraction (starts only after B.3)
- C.1 Concrete use-case definition (GATE: Opus review before C.2)
- C.2 BaseVectorStore interface
- C.3 InMemoryVectorStore implementation
- C.4 Integration tests (5+, incl. tenant isolation) + commit
- Tag: `s68-c-vector-abstraction`

### Close
- Tag: `sprint68-closed`

## Rules

1. Strict sequential — no B work while A in review (cognitive separation).
2. Max 2 iterations per gate. Third iteration = escalation, not retry.
3. Gate doc MUST contain: raw data extract, per-sample analysis, design
   proposal with evidence. Never abstract-only.
4. Pushback rights: either side may challenge a 3rd iteration as
   over-specification.
5. Tenant isolation enforced at API layer (not just DB layer) — defense
   in depth.
6. Stem-based Icelandic keywords (Lesson #19).

## Risks (from Opus review)

- Risk #1: n=6 standard queries — may need synthetic augmentation (handled in A.1).
- Risk #2: legal reference format is political — beta-lögmaður query or scraper
  preview (handled in B.1).
- Risk #3: vector abstraction over-engineering — locked to one concrete flow (C.1).
