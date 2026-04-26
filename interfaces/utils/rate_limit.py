"""Gæðatak (rate limiting) — flutt úr web_server.py (Sprint 71 A.4e)."""
import os
import time
from collections import defaultdict
from typing import Dict, List

GÆÐATAK_HÁMARK: int = int(os.environ.get("RATE_LIMIT", 20))
GÆÐATAK_GLUGGI: int = 60  # sekúndur

_gæðatak_minni: Dict[str, List[float]] = defaultdict(list)


def athuga_gæðatak(ip: str) -> bool:
    """
    Sannprófar hvort IP tala sé yfir gæðataki.
    Skilar True ef beiðni er leyfð, False ef yfir mörk.
    Notar gluggatíma (sliding window) — einfaldasta útfærslan án Redis.
    """
    núna = time.time()
    _gæðatak_minni[ip] = [t for t in _gæðatak_minni[ip] if núna - t < GÆÐATAK_GLUGGI]
    if len(_gæðatak_minni[ip]) >= GÆÐATAK_HÁMARK:
        return False
    _gæðatak_minni[ip].append(núna)
    return True


def sækja_ip(request) -> str:
    """
    Tekur CF / proxy hausana með í reikninginn.
    """
    for haus in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        gildi = request.headers.get(haus) if hasattr(request, "headers") else None
        if gildi:
            return gildi.split(",")[0].strip()
    return request.client.host if getattr(request, "client", None) else "0.0.0.0"
