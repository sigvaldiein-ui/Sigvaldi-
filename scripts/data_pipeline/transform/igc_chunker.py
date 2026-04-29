"""Breytir IGC lagatexta í chunks eftir lagagreinum (K2 Transform)."""
import re
import unicodedata
import logging
from typing import Iterator, Dict, Any

logger = logging.getLogger("alvitur.chunker")

# "1. gr.", "134. gr.", "Kap. 1.", "Kap. 134."
_GREINA_MYNSTUR = re.compile(
    r"(?:^|\n)\s*(?:(?:Kap\.)\s*(\d{1,3})|(\d{1,3})\s*\.\s*(gr\.|kap\.|tölul\.|liður|mgr\.))",
    re.IGNORECASE
)

_MAX_ORD = 300


def _telja_ord(texti: str) -> int:
    return len(texti.split())


def _hreinsa(texti: str) -> str:
    t = unicodedata.normalize("NFC", texti)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _brjota_eftir_malsgreinum(
    texti: str, title: str, source: str, section: str = "Óskipt"
) -> Iterator[Dict[str, Any]]:
    malsgreinar = re.split(r"\n\s*\n", texti)
    nuverandi_chunk = ""

    for mg in malsgreinar:
        mg = mg.strip()
        if not mg:
            continue

        if _telja_ord(nuverandi_chunk) + _telja_ord(mg) > _MAX_ORD and nuverandi_chunk:
            yield {
                "text": nuverandi_chunk.strip(),
                "metadata": {
                    "title": title,
                    "source": source,
                    "section": section,
                }
            }
            nuverandi_chunk = mg
        else:
            nuverandi_chunk += "\n\n" + mg if nuverandi_chunk else mg

    if nuverandi_chunk.strip():
        yield {
            "text": nuverandi_chunk.strip(),
            "metadata": {
                "title": title,
                "source": source,
                "section": section,
            }
        }


def _vinna_numer(match: re.Match) -> tuple[str, str] | None:
    """Dregur út (númer, tegund) úr regex matchi."""
    kap_num = match.group(1)
    gr_num = match.group(2)
    gr_tegund = match.group(3)
    
    if kap_num:
        return (kap_num, "kap")
    elif gr_num and gr_tegund:
        return (gr_num, gr_tegund.lower().rstrip("."))
    return None


def chunk_igc_document(title: str, source: str, text: str) -> Iterator[Dict[str, Any]]:
    hreinn_texti = _hreinsa(text)
    gr_skil = list(_GREINA_MYNSTUR.finditer(hreinn_texti))

    if not gr_skil:
        if _telja_ord(hreinn_texti) <= _MAX_ORD:
            yield {
                "text": hreinn_texti,
                "metadata": {
                    "title": title,
                    "source": source,
                    "section": "Óskipt",
                }
            }
        else:
            for chunk in _brjota_eftir_malsgreinum(hreinn_texti, title, source):
                yield chunk
        return

    if gr_skil[0].start() > 0:
        formali = hreinn_texti[:gr_skil[0].start()].strip()
        if formali and _telja_ord(formali) > 5:
            yield {
                "text": formali,
                "metadata": {
                    "title": title,
                    "source": source,
                    "section": "Inngangur",
                }
            }

    for i, match in enumerate(gr_skil):
        numer_tegund = _vinna_numer(match)
        if not numer_tegund:
            continue
        
        gr_num, gr_tegund = numer_tegund

        start = match.start()
        end = gr_skil[i + 1].start() if i + 1 < len(gr_skil) else len(hreinn_texti)

        gr_texti = hreinn_texti[start:end].strip()
        ord_fjoldi = _telja_ord(gr_texti)

        section = f"{gr_num}. {gr_tegund}"

        if ord_fjoldi <= _MAX_ORD:
            yield {
                "text": gr_texti,
                "metadata": {
                    "title": title,
                    "source": source,
                    "section": section,
                }
            }
        else:
            logger.debug(f"Stór grein ({ord_fjoldi} orð): {section}")
            for undir_chunk in _brjota_eftir_malsgreinum(gr_texti, title, source, section):
                yield undir_chunk


# --- Smoke test ---
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, "/workspace/Sigvaldi-")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    from scripts.data_pipeline.sources.igc_fetcher import fetch_igc_stream

    print("=== IGC Chunker Smoke Test ===\n")
    
    for doc in fetch_igc_stream("law_law", limit=2):
        print(f" Titill: {doc['title']}")
        print(f" Heimild: {doc['source']}")
        print(f"  Chunks:")
        
        for i, chunk in enumerate(chunk_igc_document(doc["title"], doc["source"], doc["text"])):
            ord_talning = _telja_ord(chunk["text"])
            texti_brot = chunk["text"][:120].replace("\n", " ")
            print(f"    [{i+1}] {chunk['metadata']['section']} ({ord_talning} orð): {texti_brot}...")
        
        print()
    
    print(" Smoke test klárt!")
