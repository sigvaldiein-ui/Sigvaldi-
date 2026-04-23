# PDF Layout Evaluation (Phase 1 A2, 2026-04-22)

## Availability on PyPI
- pymupdf4llm: latest 1.27.2.2 (matches our PyMuPDF 1.27.2.2)
- pymupdf-layout: latest 1.27.2.2 (matches our PyMuPDF 1.27.2.2)
- Neither currently installed on the pod.

## Requirements
- CPU-only. No GPU needed. Important because our A40 free memory
  is only 3722 MiB at capture.
- Dependencies pulled in: networkx, numpy, onnxruntime, pyyaml.

## Current packaging (per official PyMuPDF docs)
- Layout is bundled with pymupdf4llm: pip install pymupdf4llm is
  sufficient.
- Activation pattern at runtime:
    import pymupdf.layout
    pymupdf.layout.activate()
    import pymupdf4llm
- Without the activate() call, pymupdf4llm runs without layout.

## Value for S65
- Primary benefit: better borderless PDF table detection,
  which was our Sprint 64 known limit.
- Secondary: clean markdown/JSON extraction for RAG ingestion.
- 10x faster than vision-based tools on CPU.

## Recommendation
- DEFER actual install to Phase 3 A-cleanup, behind a capability
  flag (pdf_tables.py tries pymupdf4llm first, falls back to
  current PyMuPDF find_tables then pdfplumber).
- Before install, run pip install --dry-run to verify no version
  conflict with existing pandas, pydantic, langchain stack.
- Add a small smoke fixture: a borderless table PDF to prove
  layout lift over current 0-table result.

## Risks
- onnxruntime pull-in adds ~150 MB to image; acceptable on 208T
  persistent volume, but watch container rebuild size.
- Layout activate() is a global switch; must not break existing
  find_tables() behaviour on bordered fixtures. Parity test needed.

## Status
- Discovery only. No installs performed in Phase 1.
