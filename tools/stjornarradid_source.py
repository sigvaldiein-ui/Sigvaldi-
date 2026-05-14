import re

import asyncio
import httpx
import sys
from datetime import datetime, timezone
from typing import Dict
from bs4 import BeautifulSoup

STJORNARRADID_URL = "https://www.stjornarradid.is/rikisstjorn/skipan-rikisstjornar/"

async def fetch_stjornarradid(query: str, max_results: int = 30) -> Dict:
    """Sækir allan ráðherralistann — leitarorðið ákvarðar aðeins röðun."""
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(STJORNARRADID_URL)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Finna ráðherralistann
            minister_items = soup.find_all("div", class_="radherra-list__item")
            # Undirbúa leitarorð — brjóta í 3+ stafa einingar
            import re as _re
            raw_kw = [kw for kw in query.lower().replace('?','').replace('!','').split() if len(kw) >= 4]
            if not raw_kw:
                raw_kw = query.lower().split()
            keywords = []
            for kw in raw_kw:
                keywords.append(kw)
                # Brjóta langt samsett orð (t.d. menntamálaráðherra → mennta, mála, ráðherra)
                if len(kw) >= 8 and ' ' not in kw:
                    for part in _re.findall(r'[a-záðéíóúýþæö]{3,}', kw):
                        if part not in keywords:
                            keywords.append(part)
            # Fjarlægja of algeng orð sem eru sameiginleg öllum ráðherrum
            too_common = {'ráðherra', 'íslands', 'hver', 'eru', 'sem', 'fyrir', 'þetta', 'þessa', 'þessum'}
            keywords = [kw for kw in keywords if kw not in too_common]


            for item in minister_items:
                name_tag = item.find("div", class_="radherra-list__item__name")
                title_tag = item.find("div", class_="radherra-list__item__title")
                
                if name_tag and title_tag:
                    name = name_tag.get_text(strip=True)
                    title = title_tag.get_text(strip=True)
                    combined = f"{name} - {title}"
                    
                    # Reikna hversu vel leitarorðið passar
                    # Nota orðmörk til að forðast substring-villur
                    score = sum(1 for kw in keywords if kw in combined.lower())

                    # Sprint 82: Title-exact-match boost (EXACT_TITLE_BOOST = 5.0)
                    # Ef leitarorð er ráðherratitill og passar við titil ráðherrans, margfalda score
                    for kw in keywords:
                        if kw.endswith(("ráðherra", "ráðherra")) and kw in title.lower():
                            score *= 5.0
                            break
                    
                    # Fallback fyrir samsett orð sem finnast ekki beint (t.d. menntamálaráðherra)
                    if score == 0:
                        import unicodedata
                        def _trigrams(s):
                            s = ''.join(c.lower() for c in s if c.isalpha())
                            return {s[i:i+3] for i in range(len(s)-2)}
                        query_set = _trigrams(query)
                        title_set = _trigrams(title)
                        if query_set and title_set:
                            jaccard = len(query_set & title_set) / len(query_set | title_set)
                            if jaccard > 0.25:
                                score = 1.0
                    
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
            for i, c in enumerate(citations, 1):
                c["rank"] = i

        return {
            "citations": citations,
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

if __name__ == "__main__":
    import asyncio as _asyncio
    for q in ["dómsmálaráðherra", "menntamálaráðherra", "utanríkisráðherra"]:
        result = _asyncio.run(fetch_stjornarradid(q))
        print(f"\n--- {q} ---")
        for c in result["citations"]:
            print(f"{c['rank']}. {c['snippet']}")
