
"""Span-varðveitandi normalisering + kandídatar fyrir PII Sentry."""
import re
from typing import List, Tuple

OCR_MAP = str.maketrans({"l": "1", "I": "1", "O": "0", "o": "0"})
SEP = set(" \t.-_/~–—()[]{}:,;!?\"'")

# Íslensk talnaorð → tölur
WORDNUMS = {
    "núll": "0", "einn": "1", "tveir": "2", "þrír": "3", "fjórir": "4",
    "fimm": "5", "sex": "6", "sjö": "7", "átta": "8", "níu": "9",
    "tíu": "10", "ellefu": "11", "tólf": "12", "þrettán": "13",
    "fjórtán": "14", "fimmtán": "15", "sextán": "16", "sautján": "17",
    "átján": "18", "nítján": "19", "tuttugu": "20", "þrjátíu": "30",
    "fjörutíu": "40", "fimmtíu": "50", "sextíu": "60", "sjötíu": "70",
    "áttatíu": "80", "níutíu": "90", "hundrað": "100",
}

def wordnums_to_digits(text: str) -> str:
    """Skipta íslenskum talnaorðum út fyrir tölur. Notar einfalda replace-lúppu."""
    result = text.lower()
    for word, digit in WORDNUMS.items():
        result = result.replace(word, digit)
    return result

def digit_runs(text: str, max_gap: int = 3) -> List[Tuple[str, List[int]]]:
    """Skilar (digits, offsets) — runur af tölum þar sem skiltákn/bil
    (≤max_gap) á milli eru hunsuð. Hver tala heldur upprunalegu offseti."""
    text_ocr = text.translate(OCR_MAP)
    runs, cur_d, cur_o, gap = [], [], [], 0
    for i, ch in enumerate(text_ocr):
        if ch.isdigit():
            cur_d.append(ch); cur_o.append(i); gap = 0
        elif ch in SEP and cur_d and gap < max_gap:
            gap += 1
        else:
            if len(cur_d) >= 6:
                runs.append(("".join(cur_d), cur_o))
            cur_d, cur_o, gap = [], [], 0
    if len(cur_d) >= 6:
        runs.append(("".join(cur_d), cur_o))
    return runs
