#!/usr/bin/env python3
import re
from urllib.parse import urlparse

TRAUST = [
    "althingi.is","stjornarradid.is","government.is","island.is",
    "ruv.is","mbl.is","visir.is","wikipedia.org","hi.is","ru.is",
    "landlaeknir.is","skatturinn.is","almannaromur.is","arnastofnun.is",
    "vedur.is","lhi.is","samgongustofa.is","utl.is","mcc.is",
    ".gov",".edu"
]

def score_url(url: str) -> float:
    try:
        domain = urlparse(url).netloc.lower().replace("www.","")
        for t in TRAUST:
            if t in domain:
                return 0.9 if "wikipedia" not in t else 0.8
        if domain.endswith(".is"):
            return 0.6
        if domain.endswith(".com") or domain.endswith(".net"):
            return 0.3
        return 0.2
    except:
        return 0.1

def score_sources(urls: list) -> dict:
    if not urls:
        return {"average_score": 0.0, "trusted": [], "untrusted": [], "warning": True}
    scores = [(u, score_url(u)) for u in urls]
    trusted = [u for u,s in scores if s >= 0.6]
    untrusted = [u for u,s in scores if s < 0.6]
    avg = sum(s for _,s in scores) / len(scores)
    return {"average_score": round(avg,2), "trusted": trusted, "untrusted": untrusted, "warning": avg < 0.5}

def get_warning_text() -> str:
    return "\n\n⚠️ Athugid: Thetta svar byggir ad hluta a ostadfestum heimildum. Takid upplysingunum med fyrirvara."

if __name__ == "__main__":
    print("CODE FREEZE - Standalone eining")
    print(score_sources(["https://ruv.is/frett", "https://random-blog.com"]))
