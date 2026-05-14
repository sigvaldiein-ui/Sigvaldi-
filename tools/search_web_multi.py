"""
Sprint 80c v2 RC2 — Multi-source RRF Web Search
Orkestrator sem safnar saman Stjórnarráði, Stjórnartíðindum, Mojeek,
og Wayback (söguleg gögn), og sameinar með RRF (k=60).
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List

import httpx

from tools.stjornarradid_source import fetch_stjornarradid
from tools.stjornartidindi_source import fetch_stjornartidindi
from tools.sources.wayback_source import fetch_wayback_snapshots
from core.citation_schema import build_citation, deduplicate, render_markdown, simhash_64

SOURCE_WEIGHTS = {
    "stjornarradid": 2.0,
    "stjornartidindi": 2.0,
    "mojeek": 1.0,
    "wayback": 0.8,
}

MOJEEK_BASE = "https://api.mojeek.com/search"

def _simplify_query_for_mojeek(query: str) -> str:
    import re
    stop = {"hver","hvad","hvort","hvar","hvenaer","hvernig","hvers","vegna",
            "er","var","verdur","munu","i","a","ad","og","eda","med","fra","til",
            "the","is","are","of","in","to","for","what","who","when","where","how","why"}
    cleaned = re.sub(r"[?!.,;:]", "", query.lower())
    words = [w for w in cleaned.split() if w not in stop and len(w) > 2]
    return " ".join(words) if words else query.strip()

async def _fetch_mojeek(query: str, max_results: int = 5) -> Dict:
    api_key = os.environ.get("MOJEEK_API_KEY", "")
    if not api_key:
        return {"citations": [], "source": "mojeek", "error": "MOJEEK_API_KEY missing", "raw_count": 0}

    params = {"api_key": api_key, "q": _simplify_query_for_mojeek(query), "fmt": "json"}
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(MOJEEK_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {"citations": [], "source": "mojeek", "error": str(e), "raw_count": 0}

    if data.get("response", {}).get("status") != "OK":
        return {"citations": [], "source": "mojeek", "error": "Mojeek API bad status", "raw_count": 0}

    raw_results = data.get("response", {}).get("results", [])
    if not raw_results:
        return {"citations": [], "source": "mojeek", "raw_count": 0}

    citations = []
    for i, raw in enumerate(raw_results[:max_results], 1):
        c = build_citation(raw, source="mojeek", rank=i)
        c["accessed_at"] = datetime.now(timezone.utc).isoformat()
        citations.append(c)

    return {"citations": citations, "source": "mojeek", "raw_count": len(raw_results)}

def rrf_merge(source_groups: List[Dict], k: int = 60) -> List[Dict]:
    scores: Dict[str, dict] = {}
    for group in source_groups:
        w = SOURCE_WEIGHTS.get(group.get("source", ""), 1.0)
        for citation in group.get("citations", []):
            if not citation.get("simhash"):
                title = citation.get("title", "") or ""
                snippet = citation.get("snippet", "") or ""
                citation["simhash"] = simhash_64(f"{title} {snippet}")
            url = citation.get("url", "")
            rank = citation.get("rank", 99)
            rrf = w * (1.0 / (k + rank))
            if url not in scores or scores[url]["rrf"] < rrf:
                scores[url] = {**citation, "rrf": rrf, "_weight": w}

    merged = sorted(scores.values(), key=lambda x: -x["rrf"])
    for i, c in enumerate(merged, 1):
        c["rank"] = i
    return merged

async def search_web_multi(query: str, max_results: int = 5) -> Dict:
    # Keyra allar fjórar heimildir samtímis
    stjornar, tidindi, mojeek, wayback = await asyncio.gather(
        fetch_stjornarradid(query, max_results),
        fetch_stjornartidindi(query, max_results),
        _fetch_mojeek(query, max_results),
        fetch_wayback_snapshots(query, max_results),
    )

    # Sameina með RRF
    merged = rrf_merge([stjornar, tidindi, mojeek, wayback])
    merged = deduplicate(merged)
    merged = merged[:max_results]
    md = render_markdown(merged)

    return {
        "citations": merged,
        "markdown": md,
        "raw_count": sum(g.get("raw_count", 0) for g in [stjornar, tidindi, mojeek, wayback]),
    }

if __name__ == "__main__":
    async def test():
        res = await search_web_multi("forsætisráðherra", max_results=5)
        print(res["markdown"])
        print(f"\nHeimildir: {len(res['citations'])}")
        sources = set(c.get("source") for c in res["citations"])
        print(f"Sources: {sources}")
    asyncio.run(test())
