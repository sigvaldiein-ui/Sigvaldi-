"""Unified tabular dispatcher. Never raises; returns [] on any failure."""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import pandas as pd

EXT_PDF = {".pdf"}
EXT_DOCX = {".docx", ".doc"}
EXT_XLSX = {".xlsx", ".xls"}
EXT_CSV = {".csv"}

def _ext(path: Path, file_type: Optional[str]) -> str:
    if file_type:
        ft = file_type.lower().strip()
        if ft.startswith("."):
            return ft
        if "pdf" in ft: return ".pdf"
        if "word" in ft or "docx" in ft: return ".docx"
        if "sheet" in ft or "excel" in ft or "xlsx" in ft: return ".xlsx"
        if "csv" in ft: return ".csv"
    return path.suffix.lower()

def extract_tables(path: str | Path, file_type: Optional[str] = None) -> List[pd.DataFrame]:
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size == 0:
            return []
        ext = _ext(p, file_type)
        if ext in EXT_PDF:
            from adapters.pdf_tables import extract_pdf_tables
            return extract_pdf_tables(p) or []
        if ext in EXT_DOCX:
            from adapters.docx_tables import extract_docx_tables
            return extract_docx_tables(p) or []
        if ext in EXT_XLSX:
            try:
                sheets = pd.read_excel(str(p), sheet_name=None)
                return [df for df in sheets.values() if df is not None and df.shape[1] > 0]
            except Exception:
                return []
        if ext in EXT_CSV:
            try:
                return [pd.read_csv(str(p))]
            except Exception:
                return []
        return []
    except Exception:
        return []
