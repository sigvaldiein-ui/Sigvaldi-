"""DOCX table adapter. Never raises; returns [] on any failure."""
from __future__ import annotations
from pathlib import Path
from typing import List
import pandas as pd

def extract_docx_tables(path: str | Path) -> List[pd.DataFrame]:
    try:
        from docx import Document
    except Exception:
        return []
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return []
    try:
        doc = Document(str(p))
    except Exception:
        return []
    out: List[pd.DataFrame] = []
    for tbl in getattr(doc, "tables", []) or []:
        try:
            rows = [[cell.text for cell in row.cells] for row in tbl.rows]
            if not rows or not rows[0]:
                continue
            header, *data = rows
            if not data:
                df = pd.DataFrame(columns=header)
            else:
                df = pd.DataFrame(data, columns=header)
            if df.shape[1] > 0:
                out.append(df)
        except Exception:
            continue
    return out
