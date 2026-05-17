"""
Sprint 86 — Vísindavefur HÍ Source
Sækir fræðileg svör úr RSS straumi Vísindavefsins.
Vægi: 1.2× (fræðilegt efni, íslenskt, varanlegt)
"""
import asyncio
import httpx
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict

VISINDAVEFUR_RSS_URL = "https://www.visindavefur.is/visindavefur.rss"

async def fetch_visindavefur(query: str, max_results: int = 5) -> Dict:
    """
    Sækir Vísindavef HÍ RSS og leitar eftir fyrirspurn.
    Skilar dict með citations og lýsigögnum.
    """
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(VISINDAVEFUR_RSS_URL)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            keywords = query.lower().split()
            items = root.findall(".//item")
            matches = []

            for item in items:
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")

                if any(kw in title.lower() or kw in description.lower() for kw in keywords):
                    matches.append({
                        "title": title,
                        "description": description,
                        "link": link,
                    })

            for i, match in enumerate(matches[:max_results], 1):
                citations.append({
                    "title": match["title"],
                    "url": match["link"],
                    "snippet": match["description"][:300] if match["description"] else "",
                    "source": "visindavefur",
                    "tier": "academic",
                    "score": 0.0,
                    "rank": i,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })

        return {
            "citations": citations,
            "source": "visindavefur",
            "raw_count": len(matches),
        }
    except httpx.TimeoutException:
        print("Visindavefur API: timeout eftir 10 sek", file=sys.stderr)
        return {"citations": [], "source": "visindavefur", "error": "timeout", "raw_count": 0}
    except httpx.HTTPStatusError as e:
        print(f"Visindavefur API: HTTP {e.response.status_code}", file=sys.stderr)
        return {"citations": [], "source": "visindavefur", "error": f"http_{e.response.status_code}", "raw_count": 0}
    except ET.ParseError as e:
        print(f"Visindavefur API: XML parse error — {e}", file=sys.stderr)
        return {"citations": [], "source": "visindavefur", "error": "xml_parse_error", "raw_count": 0}
    except Exception as e:
        print(f"Visindavefur API: óvænt villa — {type(e).__name__}: {e}", file=sys.stderr)
        return {"citations": [], "source": "visindavefur", "error": f"unexpected_{type(e).__name__}", "raw_count": 0}


# Prófun ef keyrt beint
if __name__ == "__main__":
    async def test():
        result = await fetch_visindavefur("hantaveira")
        print(f"Fjöldi: {result['raw_count']}")
        for c in result["citations"]:
            print(f"{c['rank']}. {c['snippet'][:150]}...")

    asyncio.run(test())
