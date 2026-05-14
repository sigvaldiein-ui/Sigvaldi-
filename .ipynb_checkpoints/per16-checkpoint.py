import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Optional

STJORNARRADID_URL = "https://www.stjornarradid.is/rikisstjorn/skipan-rikisstjornar/"

async def fetch_stjornarradid(query: str, max_results: int = 5) -> Dict:
    """
    Sækir skipan ríkisstjórnar og reynir að finna viðeigandi upplýsingar.
    """
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(STJORNARRADID_URL)
            resp.raise_for_status()
            html = resp.text

            # Einföld leit í HTML eftir <li> eða <td> sem innihalda leitarorð
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Finna alla lista-þætti sem gætu innihaldið ráðherra
            candidates = soup.find_all(["li", "td", "p", "h3", "h4"])
            matches = []
            keywords = query.lower().split()
            
            for tag in candidates:
                text = tag.get_text(strip=True)
                if text and any(kw in text.lower() for kw in keywords):
                    matches.append(text[:300])

            # Búa til citations úr fyrstu niðurstöðum
            for i, match in enumerate(matches[:max_results], 1):
                citations.append({
                    "title": match[:100],
                    "url": STJORNARRADID_URL,
                    "snippet": match,
                    "source": "stjornarradid",
                    "rank": i,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })

        return {
            "citations": citations,
            "source": "stjornarradid",
            "raw_count": len(matches),
        }
    except Exception as e:
        return {"citations": [], "source": "stjornarradid", "error": str(e), "raw_count": 0}

# Prófun ef keyrt beint
if __name__ == "__main__":
    result = asyncio.run(fetch_stjornarradid("forsætisráðherra"))
    for c in result["citations"]:
        print(f"{c['rank']}. {c['snippet'][:150]}...")
    print(f"\nFjöldi: {result['raw_count']}")