import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Optional

STJORNARTIDINDI_RSS_URL = "https://api.stjornartidindi.is/api/v1/rss/a-deild"

async def fetch_stjornartidindi(query: str, max_results: int = 5) -> Dict:
    """
    Sækir Stjórnartíðindi RSS og leitar eftir fyrirspurn.
    """
    citations = []
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(STJORNARTIDINDI_RSS_URL)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

            keywords = query.lower().split()
            items = root.findall(".//item")

            matches = []
            for item in items:
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")

                if any(kw in title.lower() or kw in description.lower() for kw in keywords):
                    matches.append({
                        "title": title,
                        "description": description,
                        "link": link,
                        "pub_date": pub_date,
                    })

            for i, match in enumerate(matches[:max_results], 1):
                citations.append({
                    "title": match["title"],
                    "url": match["link"],
                    "snippet": match["description"],
                    "source": "stjornartidindi",
                    "rank": i,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })

        return {
            "citations": citations,
            "source": "stjornartidindi",
            "raw_count": len(matches),
        }
    except Exception as e:
        return {"citations": [], "source": "stjornartidindi", "error": str(e), "raw_count": 0}

# Prófun ef keyrt beint
if __name__ == "__main__":
    result = asyncio.run(fetch_stjornartidindi("lög"))
    for c in result["citations"]:
        print(f"{c['rank']}. {c['snippet'][:150]}...")
    print(f"\nFjöldi: {result['raw_count']}")