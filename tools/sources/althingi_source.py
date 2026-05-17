"""
Sprint 86 — Althingi Source
Sækir þingmál úr XML API althingi.is.
Vægi: 1.5× (skv. SPRINT80C_V2_STRATEGY.md)
"""
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List

ALTHINGI_XML_URL = "https://www.althingi.is/altext/xml/thingmalalisti/"


async def fetch_althingi(query: str, max_results: int = 5) -> Dict:
    """
    Sækir þingmál af althingi.is og leitar eftir fyrirspurn.
    Skilar dict með citations og lýsigögnum.
    """
    citations = []
    try:
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(ALTHINGI_XML_URL)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            keywords = query.lower().split()
            matches = []

            for mal in root.findall(".//mál"):
                title = mal.findtext("málsheiti", "")
                description = mal.findtext("efnisgreining", "")
                html_link = mal.findtext("html", "")
                malnr = mal.get("málsnúmer", "")
                thingnr = mal.get("þingnúmer", "")

                combined = f"{title} {description}".lower()
                score = sum(1 for kw in keywords if kw in combined)

                if score > 0:
                    matches.append({
                        "title": title,
                        "description": description,
                        "html_link": html_link,
                        "malnr": malnr,
                        "thingnr": thingnr,
                        "score": score,
                    })

            matches.sort(key=lambda m: -m["score"])

            for i, match in enumerate(matches[:max_results], 1):
                citations.append({
                    "title": match["title"],
                    "url": match["html_link"],
                    "snippet": match["description"] or f"Þingmál {match['malnr']} á {match['thingnr']}. þingi",
                    "source": "althingi",
                    "tier": "government",
                    "score": match["score"],
                    "rank": i,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })

        return {
            "citations": citations,
            "source": "althingi",
            "raw_count": len(matches),
        }

    except httpx.TimeoutException:
        print("Althingi API: timeout eftir 15 sek", file=__import__('sys').stderr)
        return {"citations": [], "source": "althingi", "error": "timeout", "raw_count": 0}
    except httpx.HTTPStatusError as e:
        print(f"Althingi API: HTTP {e.response.status_code}", file=__import__('sys').stderr)
        return {"citations": [], "source": "althingi", "error": f"http_{e.response.status_code}", "raw_count": 0}
    except ET.ParseError as e:
        print(f"Althingi API: XML parse error — {e}", file=__import__('sys').stderr)
        return {"citations": [], "source": "althingi", "error": "xml_parse_error", "raw_count": 0}
    except Exception as e:
        print(f"Althingi API: óvænt villa — {type(e).__name__}: {e}", file=__import__('sys').stderr)
        return {"citations": [], "source": "althingi", "error": f"unexpected_{type(e).__name__}", "raw_count": 0}


# Prófun ef keyrt beint
if __name__ == "__main__":
    async def test():
        result = await fetch_althingi("persónuvernd")
        print(f"Fjöldi: {result['raw_count']}")
        for c in result["citations"]:
            print(f"{c['rank']}. {c['snippet'][:150]}...")

    asyncio.run(test())
