"""
Sprint 80c — Fail-Secure PII Filter
Scans query for Icelandic personal identifiers before external search.
If PII detected or filter fails → blocks external call → returns None (caller falls back to RAG).
"""
import re
import logging

logger = logging.getLogger("alvitur.pii_filter")

# Compile once
_KENNITALA = re.compile(r'\b\d{6}-\d{4}\b')
_SIMI = re.compile(r'\b\d{3}[- ]?\d{4}\b')
_NETRANG = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')


def contains_pii(query: str) -> bool:
    """
    Returns True if any PII pattern matches.
    Never raises — returns True on exception (fail-secure).
    """
    if not query or not isinstance(query, str):
        return True  # Fail-secure: block if uncertain
    try:
        q = query.strip()
        if not q:
            return True
        if _KENNITALA.search(q):
            logger.info("PII blocked: kennitala")
            return True
        if _SIMI.search(q):
            logger.info("PII blocked: símanúmer")
            return True
        if _NETRANG.search(q):
            logger.info("PII blocked: tölvupóstur")
            return True
        return False
    except Exception as e:
        logger.error(f"PII filter exception: {type(e).__name__}: {e}")
        return True  # Fail-secure: block on error


def mask_pii_for_log(query: str) -> str:
    """
    Returns query with PII replaced by ***MASKED*** for audit log.
    Never raises — returns original on exception.
    """
    if not query or not isinstance(query, str):
        return "***EMPTY***"
    try:
        q = query.strip()
        q = _KENNITALA.sub("***KT***", q)
        q = _SIMI.sub("***SIMI***", q)
        q = _NETRANG.sub("***NETFANG***", q)
        return q
    except Exception:
        return "***MASK_ERROR***"
