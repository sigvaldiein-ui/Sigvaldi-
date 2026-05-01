# OCR Feasibility (Phase 1 A3, 2026-04-22)

## Current state on pod
- tesseract binary: NOT installed
- apt-cache policy tesseract-ocr: empty (apt index may be stale)
- easyocr (pip): available 1.7.2, not installed
- pytesseract (pip): available 0.3.13, not installed

## Option 1: tesseract via apt
- Command: apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-isl
- Pros: mature, fast, small footprint, good Icelandic model.
- Cons: installs into overlay (/), LOST on pod restart.
  Requires container rebuild for persistence (we do not own spec yet).
- Verdict: viable only once container spec is owned.

## Option 2: easyocr via pip
- Command: pip install easyocr
- Pros: pure-Python install, persists in /workspace venv if we
  set one up; supports 80+ languages including Icelandic.
- Cons: pulls torch and torchvision (~2 GB); default runs on GPU
  which conflicts with our 3722 MiB GPU free. Can be forced to CPU
  but will be slow for large docs.
- Verdict: backup option. Heavy dependency footprint.

## Option 3: pytesseract + tesseract apt binary
- Same persistence problem as Option 1 plus Python wrapper.
- No advantage over Option 1 alone for now.
- Verdict: skip.

## Recommendation for Sprint 65
- DEFER OCR to Sprint 66 once container spec is formally owned.
- In S65 we add the hook point only: adapters/pdf_tables.py gets
  an ocr_fallback() stub that returns [] when OCR is not wired.
  This keeps the contract in place so S66 can drop in either
  tesseract or easyocr without touching callers.
- This preserves the S65 hard gate: no system-level changes that
  could break PROD.

## Risks if OCR is rushed into S65
- apt install breaks if network policies or proxy layer change.
- easyocr torch install can exceed overlay disk and fail silently.
- GPU memory pressure under concurrent LLM + easyocr.

## Action in S65
- Add empty ocr_fallback(path) -> List[pd.DataFrame] in pdf_tables.py
  that logs "ocr_not_configured" and returns [].
- Document in SPRINT65.md known limit.
