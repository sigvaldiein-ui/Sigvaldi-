import re

import asyncio
import httpx
import sys
from datetime import datetime, timezone
from typing import Dict
from bs4 import BeautifulSoup

STJORNARRADID_URL = "https://www.stjornarradid.is/rikisstjorn/skipan-rikisstjornar/"

async def fetch_stjornarradid(query: str, max_results: int = 5) -> Dict:
    """Sækir allan ráðherralistann — leitarorðið ákvarðar aðeins röðun."""
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(STJORNARRADID_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Finna ráðherralistann
            minister_items = soup.find_all("div", class_="radherra-list__item")
            # Bæta við sérstöku leitarorði fyrir titilinn
            title_keywords = ''.join(c for c in query.lower() if c.isalpha() or c.isspace()).split()
            # Sía út stoppstafir (<4 stafir) til að forðast substring-villur
            keywords = [kw for kw in query.lower().replace('?','').replace('!','').split() if len(kw) >= 4]
            if not keywords:
                keywords = query.lower().split()


            for item in minister_items:
                name_tag = item.find("div", class_="radherra-list__item__name")
                title_tag = item.find("div", class_="radherra-list__item__title")
                
                if name_tag and title_tag:
                    name = name_tag.get_text(strip=True)
                    title = title_tag.get_text(strip=True)
                    combined = f"{name} - {title}"
                    
                    # Reikna hversu vel leitarorðið passar
                    # Nota orðmörk til að forðast substring-villur
                    score = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", combined.lower()))
                    
                    citations.append({
                        "title": combined,
                        "url": STJORNARRADID_URL,
                        "snippet": f"{name} er {title} í ríkisstjórn Íslands.",
                        "source": "stjornarradid",
                        "score": score,
                        "rank": 0,
                        "accessed_at": datetime.now(timezone.utc).isoformat(),
                    })

            # Raða eftir score (reiknað hér að ofan), svo stafrófsröð
            citations.sort(key=lambda c: (-c.get("score", 0), c["title"]))
            for i, c in enumerate(citations[:max_results], 1):
                c["rank"] = i

        return {
            "citations": citations[:max_results],
            "source": "stjornarradid",
            "raw_count": len(citations),
        }
    except httpx.TimeoutException:
        print("Stjornarradid API: timeout eftir 10 sek", file=sys.stderr)
        return {"citations": [], "source": "stjornarradid", "error": "timeout", "raw_count": 0}
    except httpx.HTTPStatusError as e:
        print(f"Stjornarradid API: HTTP {e.response.status_code}", file=sys.stderr)
        return {"citations": [], "source": "stjornarradid", "error": f"http_{e.response.status_code}", "raw_count": 0}
    except Exception as e:
        print(f"Stjornarradid API: óvænt villa — {type(e).__name__}: {e}", file=sys.stderr)
        return {"citations": [], "source": "stjornarradid", "error": f"unexpected_{type(e).__name__}", "raw_count": 0}
        return {"citations": [], "source": "stjornarradid", "error": str(e), "raw_count": 0}

if __name__ == "__main__":
    import asyncio as _asyncio
    for q in ["dómsmálaráðherra", "menntamálaráðherra", "utanríkisráðherra"]:
        result = _asyncio.run(fetch_stjornarradid(q))
        print(f"\n--- {q} ---")
        for c in result["citations"]:
            print(f"{c['rank']}. {c['snippet']}")
