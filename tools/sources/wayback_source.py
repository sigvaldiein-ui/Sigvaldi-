"""
Sprint 80c v2 RC2 — Wayback CDX source.
Flettir upp sögulegum .is vefsíðum í gegnum Wayback CDX API.
"""
import requests
from datetime import datetime, timezone
from typing import Dict

CDX_URL = "http://web.archive.org/cdx/search/cdx"

async def fetch_wayback_snapshots(query: str, max_results: int = 3) -> Dict:
    """Leitar að eldri útgáfum af .is síðum."""
    citations = []
    try:
        params = {
            "url": query if "://" in query else f"{query}",
            "output": "json",
            "limit": max_results,
            "fl": "timestamp,original,statuscode"
        }
        resp = requests.get(CDX_URL, params=params, timeout=4)
        resp.raise_for_status()
        data = resp.json()

        if len(data) < 2:
            return {"citations": [], "source": "wayback", "raw_count": 0}

        for row in data[1:max_results + 1]:
            if len(row) >= 3:
                ts, url, sc = row[0], row[1], row[2]
                citations.append({
                    "title": url,
                    "url": f"https://web.archive.org/web/{ts}/{url}",
                    "snippet": f"Snapshot frá {ts[:4]}-{ts[4:6]}-{ts[6:8]} — Status {sc}",
                    "source": "wayback",
                    "rank": 0,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })

        citations.sort(key=lambda c: c["url"], reverse=True)
        for i, c in enumerate(citations[:max_results], 1):
            c["rank"] = i

        return {"citations": citations[:max_results], "source": "wayback", "raw_count": len(data) - 1}
    except Exception as e:
        return {"citations": [], "source": "wayback", "error": str(e), "raw_count": 0}
