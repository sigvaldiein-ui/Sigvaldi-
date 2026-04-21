"""
Sprint 62 Patch A.1: Add missing _is_beta definition before use at line 3208.

Problem: NameError: name '_is_beta' is not defined
 - Line 3208 uses _is_beta in quota check
 - Line 3448 defines it (240 lines too late)

Fix: Insert _is_beta = _er_beta_ip(_client_ip) right after _client_ip definition.
"""
import sys
from pathlib import Path

TARGET = Path("interfaces/web_server.py")

OLD = '''    _client_ip = (request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "unknown"))
    _quota_count = _quota_tracker_doc.get(_client_ip, 0) + 1
    if not _is_admin:
        _quota_tracker_doc[_client_ip] = _quota_count
    if _quota_count > FREE_QUOTA and not _is_admin and not _is_beta:'''

NEW = '''    _client_ip = (request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "unknown"))
    # Sprint 62 Patch A.1: define _is_beta early (was defined 240 lines later, causing NameError)
    try:
        _is_beta = _er_beta_ip(_client_ip)
    except Exception:
        _is_beta = False
    _quota_count = _quota_tracker_doc.get(_client_ip, 0) + 1
    if not _is_admin:
        _quota_tracker_doc[_client_ip] = _quota_count
    if _quota_count > FREE_QUOTA and not _is_admin and not _is_beta:'''

def main():
    src = TARGET.read_text()
    if "Sprint 62 Patch A.1" in src:
        print("⚠️  Patch A.1 þegar beitt. Hætti.")
        return 0
    if OLD not in src:
        print("❌ Fann ekki gamla strenginn.")
        return 1
    if src.count(OLD) > 1:
        print(f"❌ Strengur fannst {src.count(OLD)} sinnum — of áhættusamt.")
        return 1
    patched = src.replace(OLD, NEW)
    import ast
    try:
        ast.parse(patched)
    except SyntaxError as e:
        print(f"❌ Syntax villa: {e}")
        return 1
    TARGET.write_text(patched)
    print("✅ Patch A.1 beittur. Syntax OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
