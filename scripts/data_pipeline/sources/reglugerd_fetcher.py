"""Sækir og hreinsar stakar reglugerðir frá api.reglugerd.is (K2b)."""
import httpx
import logging
import unicodedata
from bs4 import BeautifulSoup
from typing import Iterator, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("alvitur.reglugerd")

BASE_URL = "https://api.reglugerd.is/api/v1/regulation/{nr}/current"

def fetch_regulation(nr: str) -> Dict[str, Any] | None:
    """Sækir JSON fyrir staka reglugerð."""
    url = BASE_URL.format(nr=nr)
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            r = client.get(url)
            if r.status_code == 200:
                return r.json()
            else:
                logger.warning(f"Gat ekki sótt {nr} - Staða: {r.status_code}")
                return None
    except Exception as e:
        logger.error(f"Villa við að sækja {nr}: {e}")
        return None

def clean_html(html_content: str) -> str:
    """Brýtur niður HTML í hreinan, NFC-staðlaðan texta."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Línubil (separator="\n") tryggir að málsgreinar renni ekki saman
    text = soup.get_text(separator="\n", strip=True)
    return unicodedata.normalize("NFC", text)

def fetcher_pipeline(nr_list: list[str]) -> Iterator[Dict[str, str]]:
    """Gagnaleiðsla (generator) sem skilar hreinum texta fyrir reglugerðir."""
    for nr in nr_list:
        data = fetch_regulation(nr)
        if not data:
            continue
            
        # Ríkið setur oftast gögnin í 'name' og 'text'
        raw_html = data.get("text", "") 
        title = data.get("name", f"Reglugerð {nr}")
        
        yield {
            "source": f"reglugerd-{nr}",
            "title": unicodedata.normalize("NFC", title),
            "text": clean_html(raw_html)
        }

if __name__ == "__main__":
    # Smoke Test
    prufu_listi = ["0104-2001", "1000-2015"]
    for chunk in fetcher_pipeline(prufu_listi):
        print(f"\n=== {chunk['title']} ({chunk['source']}) ===")
        print(chunk["text"][:300] + "...\n")
