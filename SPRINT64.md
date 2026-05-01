# Sprint 64 — Summary

**Dates:** 21-22 April 2026
**Branch:** sprint64-tracks-abc -> merged to main (4a8c2b2)
**Tag:** v0.64-complete
**Smoke baseline at merge:** 11/11 PASS on DEV 8003

## Shipped (7/7 tracks)

### Track A — Tech debt + Pydantic contract
- **A1** beta-check parity across analyze-document file, text-only, and /api/chat paths.
- **A2** models/intent.py — frozen Pydantic IntentResult (extra=forbid).
  Required fields: domain, reasoning_depth, adapter_hint, confidence_score,
  sensitivity, source_hint. Helpers: should_fallback_to_llm(0.6), is_local_only().

### Track B — Intent Gateway
- **B1** core/intent_gateway.py — rule-based classifier, ~10us/call,
  10/10 seed cases pass.
- **B2** Hooked into web_server.py at 3 sites (file, text-only, chat).
  Observability only — no pipeline routing yet (deferred to Sprint 65 Supervisor).
  _log_intent never raises; lazy import with sys.path guard.
  Also fixed latent bug: missing 'validator' import in pydantic line.

### Track C — Universal Tabular Agent
- **C1** adapters/pdf_tables.py — PyMuPDF find_tables() primary,
  pdfplumber extract_tables() fallback. Zero new system deps
  (strategy shift from camelot approved by advisory council).
- **C1-fixture-fix** sample_tables.pdf rebuilt with real grid line-strokes.
  Previous borderless fixture caused silent [] returns; verified via to_pandas().
- **C2** adapters/docx_tables.py — python-docx Document.tables -> DataFrame.
  First row = header. Never raises; returns [] on missing/corrupt/empty.
- **C3** interfaces/tabular_extractor.py — unified dispatcher.
  Extensions: .pdf, .docx/.doc, .xlsx/.xls, .csv. file_type hint supported.
- **C5** smoke T9/T10/T11 added; tail -n1 guard against PyMuPDF stdout noise.

## Known limits (carried forward)

1. **Borderless PDF tables return [].** PyMuPDF find_tables() and pdfplumber
   extract_tables() both require visual line cues. S65 plan: add_lines / clip
   region / strategy="text" per PyMuPDF-Utilities discussion #130.
2. **No OCR fallback.** Scanned PDFs return []. tesseract install deferred
   pending container spec ownership (S65).
3. **No LLM fallback for low-confidence intents.** confidence_score < 0.6
   currently does not auto-escalate; Supervisor will handle in S65.
4. **Health endpoint version string** still reads "sprint63-track-b"
   (cosmetic; fix in S65).
5. **Multi-sheet xlsx occasionally slow** — masked by 120s timeout in smoke T5.
   Observed intermittent http=000 in smoke runs (non-blocking).
6. **No /api/stats endpoint.** B2 observability logs per-request but no
   aggregate surface yet.

## Deferred to Sprint 65

- LangGraph Supervisor that consumes IntentResult for pipeline routing.
- OCR fallback (tesseract) for scanned PDFs.
- LLM fallback classification when confidence_score < 0.6.
- Container spec ownership so apt-get installs are safe.
- pymupdf-layout / pymupdf4llm evaluation for borderless PDFs
  (bundled since March 2026; 10x faster layout parsing).
- Text-only path eval accuracy regression test.
- smoke.sh split into fast (T1-T3) and full (T4+) profiles.
- /api/stats aggregate endpoint.
- Health endpoint version string bump.

## Quality gates honored

- Smoke 11/11 PASS before every commit in Track C.
- Pre-merge diagnostic confirmed main untouched since Sprint 63.
- Merge done with --no-ff for atomic revert capability.
- Post-merge smoke on main: 11/11 PASS.
- All code ASCII-only; Icelandic kept to user-facing templates.
- Backup files (.bak.*) excluded via .gitignore.

## Tags

v0.64-a1-complete, v0.64-a2-complete,
v0.64-b1-complete, v0.64-b2-complete,
v0.64-c1-complete, v0.64-c1-fixture-fix,
v0.64-c-complete, v0.64-complete

## Merge commit

4a8c2b2 Merge Sprint 64: Tracks A + B + C into main
