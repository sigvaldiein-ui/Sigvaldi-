"""Staan Web Search source — aðalleit fyrir Alvitur (Sprint 86)."""
import os, logging
from datetime import datetime, timezone
from typing import Dict, List
import httpx

logger = logging.getLogger("alvitur.staan")
STAAN_BASE = "https://api.staan.ai/v2/search/web"

async def fetch_staan(query: str, max_results: int = 5) -> Dict:
    """Kallar á Staan API og skilar citations í Alvitur-sniði."""
    token = os.environ.get("STAAN_API_KEY", "")
    if not token:
        logger.warning("STAAN_API_KEY vantar í umhverfi")
        return {"citations": [], "source": "staan", "error": "STAAN_API_KEY missing", "raw_count": 0}

    params = {
        "q": query,
        "market": "en-GB",
        "offset": 0,
        "extra_snippets": "true",
        "max_snippets": 3,
        "min_score": 0.2
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(STAAN_BASE, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"Staan API villa: {type(e).__name__}: {e}")
        return {"citations": [], "source": "staan", "error": str(e), "raw_count": 0}

    results = data.get("web", {}).get("results", [])
    citations = []
    for i, r in enumerate(results[:max_results], 1):
        # Nota extra_snippets fyrir betra samhengi ef til staðar
        snippet = r.get("snippet", "")
        if r.get("extra_snippets"):
            best = r["extra_snippets"][0]
            snippet = best.get("chunk", snippet)
        c = {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": snippet,
            "source": "staan",
            "tier": "general",
            "rank": i,
            "score": r.get("extra_snippets", [{}])[0].get("score", 0.5) if r.get("extra_snippets") else 0.5,
            "accessed_at": datetime.now(timezone.utc).isoformat()
        }
        citations.append(c)
    
    return {"citations": citations, "source": "staan", "raw_count": len(results)}
