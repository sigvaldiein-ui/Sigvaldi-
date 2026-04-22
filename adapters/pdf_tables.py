"""
Sprint 64 Track C1 — PDF table extraction adapter.

Strategy (ráðsins samþykkt stefnubreyting 22. apríl 2026):
  1. PyMuPDF find_tables() → to_pandas()        [primary, zero new deps]
  2. pdfplumber extract_tables()                 [fallback, pure-Python]
  3. OCR (tesseract)                             [deferred to Sprint 65]

Skilar List[pd.DataFrame]. Raises aldrei — skilar [] ef ekkert finnst.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

logger = logging.getLogger("alvitur.tabular.pdf")


def _extract_pymupdf(path: Union[str, Path]) -> List[pd.DataFrame]:
    """Primary: PyMuPDF 1.23+ find_tables()."""
    import fitz
    dfs: List[pd.DataFrame] = []
    doc = fitz.open(str(path))
    try:
        for page_num, page in enumerate(doc):
            try:
                tabs = page.find_tables()
            except Exception as e:
                logger.debug(f"[pymupdf] page {page_num}: find_tables raised {type(e).__name__}")
                continue
            if not tabs or not getattr(tabs, "tables", None):
                continue
            for t_idx, table in enumerate(tabs.tables):
                try:
                    df = table.to_pandas()
                    if df is not None and not df.empty:
                        dfs.append(df)
                except Exception as e:
                    logger.debug(f"[pymupdf] page {page_num} table {t_idx}: to_pandas raised {type(e).__name__}")
    finally:
        doc.close()
    return dfs


def _extract_pdfplumber(path: Union[str, Path]) -> List[pd.DataFrame]:
    """Fallback: pdfplumber extract_tables()."""
    import pdfplumber
    dfs: List[pd.DataFrame] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables() or []
            except Exception as e:
                logger.debug(f"[pdfplumber] page {page_num}: extract_tables raised {type(e).__name__}")
                continue
            for t_idx, raw in enumerate(tables):
                if not raw or len(raw) < 2:
                    continue
                try:
                    header, *rows = raw
                    df = pd.DataFrame(rows, columns=header)
                    if not df.empty:
                        dfs.append(df)
                except Exception as e:
                    logger.debug(f"[pdfplumber] page {page_num} table {t_idx}: df raised {type(e).__name__}")
    return dfs


def extract_pdf_tables(path: Union[str, Path]) -> List[pd.DataFrame]:
    """
    Public entry point. Try PyMuPDF first; fall back to pdfplumber if empty
    or if PyMuPDF raises. Returns [] for scanned/image-only PDFs (OCR in S65).
    """
    path = str(path)
    if not Path(path).exists():
        logger.warning(f"[pdf_tables] file not found: {path}")
        return []

    # Primary
    try:
        dfs = _extract_pymupdf(path)
        if dfs:
            logger.info(f"[pdf_tables] pymupdf extracted {len(dfs)} table(s) from {Path(path).name}")
            return dfs
        logger.info(f"[pdf_tables] pymupdf found 0 tables — trying pdfplumber fallback")
    except Exception as e:
        logger.warning(f"[pdf_tables] pymupdf failed ({type(e).__name__}: {e}) — trying pdfplumber")

    # Fallback
    try:
        dfs = _extract_pdfplumber(path)
        if dfs:
            logger.info(f"[pdf_tables] pdfplumber extracted {len(dfs)} table(s) from {Path(path).name}")
        else:
            logger.info(f"[pdf_tables] no tables found (scanned/image-only PDF? OCR deferred to S65)")
        return dfs
    except Exception as e:
        logger.error(f"[pdf_tables] pdfplumber also failed ({type(e).__name__}: {e})")
        return []
