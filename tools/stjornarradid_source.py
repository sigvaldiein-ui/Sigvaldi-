
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict
from bs4 import BeautifulSoup

STJORNARRADID_URL = "https://www.stjornarradid.is/rikisstjorn/skipan-rikisstjornar/"

async def fetch_stjornarradid(query: str, max_results: int = 5) -> Dict:
    """Sækir ráðherralista af Stjórnarráðssíðunni."""
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(STJORNARRADID_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            minister_items = soup.find_all("div", class_="radherra-list__item")
            keywords = query.lower().split()

            for item in minister_items:
                name_tag = item.find("div", class_="radherra-list__item__name")
                title_tag = item.find("div", class_="radherra-list__item__title")
                
                if name_tag and title_tag:
                    name = name_tag.get_text(strip=True)
                    title = title_tag.get_text(strip=True)
                    combined = f"{name} - {title}"
                    
                    if any(kw in combined.lower() for kw in keywords):
                        citations.append({
                            "title": combined,
                            "url": STJORNARRADID_URL,
                            "snippet": f"{name} er {title} í ríkisstjórn Íslands.",
                            "source": "stjornarradid",
                            "rank": len(citations) + 1,
                            "accessed_at": datetime.now(timezone.utc).isoformat(),
                        })

        return {
            "citations": citations,
            "source": "stjornarradid",
            "raw_count": len(citations),
        }
    except Exception as e:
        return {"citations": [], "source": "stjornarradid", "error": str(e), "raw_count": 0}

if __name__ == "__main__":
    import asyncio as _asyncio
    result = _asyncio.run(fetch_stjornarradid("forsætisráðherra"))
    for c in result["citations"]:
        print(f"{c['rank']}. {c['snippet']}")
    print(f"\nFjöldi: {result['raw_count']}")
