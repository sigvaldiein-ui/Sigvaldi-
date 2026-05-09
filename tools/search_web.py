"""
Sprint 80c — Web Search Tool (Mojeek)
Async wrapper for Mojeek Search API with .is boost and fail-secure PII filter.
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

import httpx

from core.pii_filter import contains_pii, mask_pii_for_log
from core.citation_schema import build_citation, deduplicate, render_markdown

logger = logging.getLogger("alvitur.search_web")

MOJEEK_BASE = "https://api.mojeek.com/search"
IS_BOOST_GENERAL = 1.5
IS_BOOST_LEGAL = 2.0

# .is domains with legal content
LEGAL_IS_DOMAINS = {
    "althingi.is",
    "stjornartidindi.is",
    "personuvernd.is",
    "haestirettur.is",
    "landsrettur.is",
    "domstolar.is",
    "stjornarradid.is",
    "sedlabanki.is",
    "logreglan.is",
    "fme.is",
}


def _is_legal_domain(url: str) -> bool:
    """Check if URL is an Icelandic legal domain."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        return host in LEGAL_IS_DOMAINS
    except Exception:
        return False


def _is_is_domain(url: str) -> bool:
    """Check if URL is any .is domain."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return host.lower().endswith(".is")
    except Exception:
        return False


def apply_boost(results: List[Dict]) -> List[Dict]:
    """Apply .is weight boost and re-sort results."""
    for r in results:
        url = r.get("url", "")
        if _is_legal_domain(url):
            r["_weight"] = IS_BOOST_LEGAL
        elif _is_is_domain(url):
            r["_weight"] = IS_BOOST_GENERAL
        else:
            r["_weight"] = 1.0
    # Sort by weighted rank: boost pushes item up equiv to rank/boost
    results.sort(key=lambda x: x.get("rank", 99) / x.get("_weight", 1.0))
    # Re-number ranks after sort
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results


async def search_web(query: str, max_results: int = 5) -> Optional[Dict]:
    """
    Execute web search via Mojeek.
    Returns dict with "citations", "markdown", "raw_count" if successful.
    Returns None if PII blocked, rate limited, or API down (caller falls back to RAG).
    """
    # PII check
    if contains_pii(query):
        logger.info("Web search blocked: PII in query")
        return None

    api_key = os.environ.get("MOJEEK_API_KEY", "")
    if not api_key:
        logger.warning("MOJEEK_API_KEY not set")
        return None

    params = {
        "api_key": api_key,
        "q": query.strip(),
        "fmt": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(MOJEEK_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        logger.error("Mojeek API timeout")
        return None
    except Exception as e:
        logger.error(f"Mojeek API error: {type(e).__name__}: {e}")
        return None

    if data.get("status") != "OK":
        logger.warning(f"Mojeek non-OK status: {data.get('status')}")
        return None

    raw_results = data.get("response", {}).get("results", [])
    if not raw_results:
        logger.info("Mojeek returned 0 results")
        return None

    citations = []
    for i, raw in enumerate(raw_results[:max_results], 1):
        c = build_citation(raw, source="mojeek", rank=i)
        c["accessed_at"] = datetime.now(timezone.utc).isoformat()
        citations.append(c)

    citations = apply_boost(citations)
    citations = deduplicate(citations)

    # Audit log
    return {
        "citations": citations,
        "markdown": render_markdown(citations),
        "raw_count": len(raw_results),
    }
