"""Sprint 62 Patch A: Skip fitz PDF-parsing for non-PDF files (xlsx/docx)."""
import sys
from pathlib import Path

TARGET = Path("interfaces/web_server.py")

OLD = '''    # — 6. Skila grunnupplýsingum (LLM greining kemur í Lag 2) —
    # Sprint 28: Einföld fitz-greining (CitationExtractor fjarlægður)
    import fitz as _fitz_inner
    with _fitz_inner.open(stream=efni, filetype="pdf") as _doc:
        sidur = len(_doc)
        _parts = []
        for _pg in _doc:
            _t = _pg.get_text().strip()
            if _t: _parts.append(_t)
'''

NEW = '''    # — 6. Skila grunnupplýsingum (LLM greining kemur í Lag 2) —
    # Sprint 62 Patch A: Only run fitz (PDF parser) for PDF files.
    # xlsx/docx already parsed above via openpyxl/python-docx.
    _parts = []
    if _filetype == 'pdf':
        import fitz as _fitz_inner
        with _fitz_inner.open(stream=efni, filetype="pdf") as _doc:
            sidur = len(_doc)
            for _pg in _doc:
                _t = _pg.get_text().strip()
                if _t: _parts.append(_t)
'''

def main():
    src = TARGET.read_text()
    if "Sprint 62 Patch A" in src:
        print("⚠️  Patch A þegar beitt. Hætti.")
        return 0
    if OLD not in src:
        print("❌ Fann ekki gamla strenginn.")
        return 1
    if src.count(OLD) > 1:
        print("❌ Strengur fannst oftar en einu sinni.")
        return 1
    patched = src.replace(OLD, NEW)
    import ast
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"❌ Syntax villa: {e}")
        return 1
    TARGET.write_text(patched)
    print("✅ Patch A beittur. Syntax OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
