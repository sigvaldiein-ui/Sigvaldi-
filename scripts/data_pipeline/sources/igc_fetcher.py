"""Sækir lagatexta úr Risamálheildinni (IGC-2024) á Hugging Face (K1)."""
import unicodedata
import logging
from typing import Iterator, Dict, Any
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("alvitur.igc_fetcher")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)

def extract_title(document: str, metadata: dict) -> str:
    """Klippir titilinn út úr skjalinu með því að nota metadata offsets."""
    try:
        t_meta = metadata.get("title", {})
        if isinstance(t_meta, dict):
            start = t_meta.get("offset")
            length = t_meta.get("length")
            if start is not None and length is not None and length > 0:
                return document[start:start+length].strip()
    except Exception:
        pass
    lines = document.strip().split("\n")
    return lines[0][:100].strip() if lines else "Óþekkt lög"

def fetch_igc_stream(config_name: str = "law_law", limit: int = 0) -> Iterator[Dict[str, Any]]:
    """Straumlesir IGC gagnasafnið af Hugging Face."""
    logger.info(f"Hef straumlestur á arnastofnun/IGC-2024 ({config_name})...")
    try:
        ds = load_dataset("arnastofnun/IGC-2024", name=config_name, split="train", streaming=True)
        
        count = 0
        for row in ds:
            if limit > 0 and count >= limit:
                break
                
            raw_text = row.get("document", "")
            if not raw_text:
                continue
                
            meta = row.get("metadata", {})
            uuid_str = row.get("uuid", "unknown-uuid")
            
            clean_text = unicodedata.normalize("NFC", raw_text)
            title = extract_title(clean_text, meta)
            clean_title = unicodedata.normalize("NFC", title)
            source_url = meta.get("source", f"igc-{config_name}-{uuid_str}")
            
            yield {
                "source": source_url,
                "title": clean_title,
                "text": clean_text
            }
            count += 1
            
    except Exception as e:
        logger.error(f"Gat ekki straumlesið {config_name}: {e}")

if __name__ == "__main__":
    import os
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    
    print("=== IGC Fetcher Prufa ===")
    for count, doc in enumerate(fetch_igc_stream("law_law", limit=3)):
        print(f"\n[{count+1}] Titill: {doc['title']}")
        print(f"Heimild: {doc['source']}")
        text_preview = doc['text'][:150].replace('\n', ' ')
        print(f"Texti (brot): {text_preview}...")
