# Container Spec (captured 2026-04-22, Phase 1 A1)

Pod: federal_harlequin_wildfowl (7ye8jghy7yl94b)

## OS
- Ubuntu 22.04.5 LTS (Jammy)
- apt and apt-get both available at /usr/bin
- root user (uid=0), full privileges

## System-level dependencies relevant to S65
- tesseract-ocr: NOT installed
- poppler-utils: NOT installed
- ghostscript:   NOT installed

## Storage
- / overlay:   40G total, 30G free (ephemeral, lost on pod restart)
- /workspace:  756T total, 208T free (persistent network volume)

## Memory
- RAM: 503Gi total, 406Gi available
- Swap: 0 (disabled)

## GPU
- NVIDIA A40
- Free memory at capture: 3722 MiB out of ~48 Gi
- Note: most GPU memory is currently held by existing local model server

## Persistence caveat
- apt installs go to overlay and will NOT survive pod restart unless
  baked into container image.
- For S65 OCR we should prefer pip-based options (easyocr, pytesseract
  with system binary) or postpone OCR until container spec is owned.

## Implications for Phase 1
- A2 pymupdf layout package: safe to pip install --dry-run test.
- A3 OCR: tesseract apt install possible but non-persistent.
  Recommend easyocr via pip as primary option; tesseract as fallback
  once container rebuild strategy is owned.
