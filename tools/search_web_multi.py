"""
Sprint 80c v2 — Multi-Source Web Search með RRF samruna.
Kallar á Stjórnarráðið og Stjórnartíðindi samhliða ásamt Mojeek.
"""

import asyncio
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

import httpx
import xml.etree.ElementTree as ET
from urllib.parse import quote

from tools.stjornarradid_source import fetch_stjornarradid
from tools.stjornartidindi_source import fetch_stjornartidindi

logger = logging.getLogger("alvitur.search_web_multi")

MOJEEK_BASE = "https://api.mojeek.com/search"

# Einföld RRF samrunaaðferð
def rrf_merge(sources: List[Dict], k: int = 60) -> List[Dict]:
    """Sameinar niðurstöður frá mörgum aðilum með RRF."""
    scored = {}
    for source in sources:
        for citation in source.get("citations", []):
            url = citation["url"]
            rank = citation.get("rank", 99)
            score = 1.0 / (k + rank)
            if url in scored:
                scored[url]["score"] += score
                scored[url]["sources"].add(citation["source"])
            else:
                citation["score"] = score
                citation["sources"] = {citation["source"]}
                scored[url] = citation

    # Raða eftir skori, hæsta fyrst
    merged = sorted(scored.values(), key=lambda x: x["score"], reverse=True)
    
    # Uppfæra upprunamerki
    for citation in merged:
        citation["source"] = "+".join(sorted(citation["sources"]))
        
    return merged

async def search_mojeke(query: str, max_results: int = 5) -> Optional[Dict]:
    """Upprunaleg Mojeek leit, aðlöguð fyrir samhæfni."""
    api_key = os.environ.get("MOJEEK_API_KEY", "")
    if not api_key:
        return {"citations": [], "source": "mojeek", "raw_count": 0}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                MOJEEK_BASE,
                params={"api_key": api_key, "q": query.strip(), "fmt": "json"}
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {"citations": [], "source": "mojeek", "error": str(e), "raw_count": 0}

    if data.get("response", {}).get("status") != "OK":
        return {"citations": [], "source": "mojeek", "raw_count": 0}

    raw_results = data.get("response", {}).get("results", [])
    if not raw_results:
        return {"citations": [], "source": "mojeek", "raw_count": 0}

    citations = []
    for i, raw in enumerate(raw_results[:max_results], 1):
        citations.append({
            "title": raw.get("title", ""),
            "url": raw.get("url", ""),
            "snippet": raw.get("desc", ""),
            "source": "mojeek",
            "rank": i,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
        })

    return {"citations": citations, "source": "mojeek", "raw_count": len(raw_results)}

async def search_web_multi(query: str, max_results: int = 5) -> Dict:
    """Kallar á allar heimildir samhliða og sameinar með RRF."""
    tasks = [
        search_mojeke(query, max_results),
        fetch_stjornarradid(query, max_results),
        fetch_stjornartidindi(query, max_results),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for r in results:
        if isinstance(r, dict) and r.get("citations"):
            valid_results.append(r)
        elif isinstance(r, Exception):
            logger.error(f"Source villa: {type(r).__name__}: {r}")

    if not valid_results:
        return {"citations": [], "raw_count": 0, "sources_queried": len(tasks)}

    merged = rrf_merge(valid_results)
    top_n = merged[:max_results]

    return {
        "citations": top_n,
        "raw_count": sum(r.get("raw_count", 0) for r in valid_results),
        "sources_queried": len(tasks),
        "sources_successful": len(valid_results),
    }

# Prófun
if __name__ == "__main__":
    async def main():
        result = await search_web_multi("forsætisráðherra")
        for c in result.get("citations", []):
            print(f"{c.get('rank', '?')}. [{c.get('source', '?')}] {c.get('snippet', '')[:100]}...")
        print(f"\nFjöldi: {result.get('raw_count', 0)}")

    asyncio.run(main())