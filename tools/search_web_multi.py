"""
Sprint 80c v2 RC2 — Multi-source RRF Web Search
Orkestrator sem safnar saman Stjórnarráði, Stjórnartíðindum, Mojeek,
og Wayback (söguleg gögn), og sameinar með RRF (k=60).
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List

import httpx
import re

from tools.sources.bin_wrapper import get_nominative
from tools.stjornarradid_source import fetch_stjornarradid
from tools.stjornartidindi_source import fetch_stjornartidindi
from tools.sources.wayback_source import fetch_wayback_snapshots
from tools.sources.staan_source import fetch_staan
from tools.sources.visindavefur_source import fetch_visindavefur
from tools.sources.althingi_source import fetch_althingi
from tools.sources.hagstofa_source import fetch_hagstofa
from core.citation_schema import build_citation, deduplicate, render_markdown, simhash_64, source_cap


BIN_STOP_WORDS = {
    "hver","hvað","hvar","hvenær","hvernig","hvort","hvers","vegna",
    "er","eru","var","voru","verður","mun","munu",
    "í","á","um","af","með","til","frá","og","eða","en",
    "núna","hér","þar","sem",
    "the","is","are","of","in","to","for","what","who","when","where","how","why",
}

def _tokenize_for_bin(query: str) -> list[str]:
    cleaned = re.sub(r'[?!.,;:\(\)\[\]\"\']', " ", query)
    parts = cleaned.split()
    tokens: list[str] = []
    for p in parts:
        t = p.strip()
        if not t:
            continue
        tokens.append(t)
    return tokens

async def lemmatize_query_terms(query: str, max_bin_calls: int = 5) -> str:
    tokens = _tokenize_for_bin(query)

    candidates: list[str] = []
    for i, t in enumerate(tokens):
        tl = t.lower()
        if tl in BIN_STOP_WORDS:
            continue
        if t.isdigit() or len(t) < 4:
            continue
        # Verja eiginnöfn / staðanöfn: sleppa öllum Titlecase orðum í V1
        if t[:1].isupper():
            continue
        candidates.append(t)

    candidates = candidates[:max_bin_calls]

    if not candidates:
        return query.strip()

    tasks = [get_nominative(c) for c in candidates]
    try:
        lemmas = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        return query.strip()

    lemma_map: dict[str, str] = {}
    for orig, res in zip(candidates, lemmas):
        if isinstance(res, Exception) or res is None:
            continue
        lemma_map[orig] = res

    normalized_tokens: list[str] = []
    for t in tokens:
        lemma = lemma_map.get(t)
        normalized_tokens.append(lemma if lemma else t)

    normalized = " ".join(normalized_tokens).strip()
    return normalized or query.strip()

SOURCE_WEIGHTS = {
    "stjornarradid": 2.0,
    "stjornartidindi": 2.0,
    "staan": 2.5,
    "mojeek": 0.7,
    "wayback": 0.8,
    "visindavefur": 1.2,
    "althingi": 1.5,
    "hagstofa": 0.7,
}

# Sprint 82: Tier multipliers fyrir source trust layer
TIER_MULTIPLIERS = {
    "government": 1.0,   # default, engin auka boost
    "legal": 0.75,       # ef Aðal velur Option A
    "general": 1.0,
}

MOJEEK_BASE = "https://api.mojeek.com/search"

def _simplify_query_for_mojeek(query: str) -> str:
    import re
    stop = {"hver","hvad","hvort","hvar","hvenaer","hvernig","hvers","vegna",
            "er","var","verdur","munu","i","a","ad","og","eda","med","fra","til",
            "the","is","are","of","in","to","for","what","who","when","where","how","why"}
    cleaned = re.sub(r"[?!.,;:]", "", query.lower())
    words = [w for w in cleaned.split() if w not in stop and len(w) > 2]
    return " ".join(words) if words else query.strip()

async def _fetch_mojeek(query: str, max_results: int = 5) -> Dict:
    api_key = os.environ.get("MOJEEK_API_KEY", "")
    if not api_key:
        return {"citations": [], "source": "mojeek", "error": "MOJEEK_API_KEY missing", "raw_count": 0}

    params = {"api_key": api_key, "q": _simplify_query_for_mojeek(query), "fmt": "json"}
    try:
        async with httpx.AsyncClient(timeout=300.0, headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}) as client:
            resp = await client.get(MOJEEK_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        logger.error("Mojeek API: timeout eftir 10 sek")
        return {"citations": [], "source": "mojeek", "error": "timeout", "raw_count": 0}
    except httpx.HTTPStatusError as e:
        logger.error(f"Mojeek API: HTTP {e.response.status_code}")
        return {"citations": [], "source": "mojeek", "error": f"http_{e.response.status_code}", "raw_count": 0}
    except json.JSONDecodeError:
        logger.error("Mojeek API: ógilt JSON svar")
        return {"citations": [], "source": "mojeek", "error": "invalid_json", "raw_count": 0}
    except Exception as e:
        logger.error(f"Mojeek API: óvænt villa — {type(e).__name__}: {e}")
        return {"citations": [], "source": "mojeek", "error": f"unexpected_{type(e).__name__}", "raw_count": 0}
        return {"citations": [], "source": "mojeek", "error": str(e), "raw_count": 0}

    if data.get("response", {}).get("status") != "OK":
        return {"citations": [], "source": "mojeek", "error": "Mojeek API bad status", "raw_count": 0}

    raw_results = data.get("response", {}).get("results", [])
    if not raw_results:
        return {"citations": [], "source": "mojeek", "raw_count": 0}

    citations = []
    for i, raw in enumerate(raw_results[:max_results], 1):
        c = build_citation(raw, source="mojeek", rank=i)
        c["accessed_at"] = datetime.now(timezone.utc).isoformat()
        citations.append(c)

    return {"citations": citations, "source": "mojeek", "raw_count": len(raw_results)}

def _relevance_score(query: str, citation: dict) -> float:
    """Reiknar einfalt Jaccard similarity milli fyrirspurnar og heimildartexta."""
    import re
    STOP_WORDS = {
        # Íslensk stopporð
        "er", "í", "og", "að", "á", "um", "af", "með", "til", "frá", "sem", "eru", "var",
        "hvað", "hver", "hvernig", "hvar", "hvenær", "hvers", "vegna",
        # Ensk stopporð
        "the", "is", "are", "of", "in", "to", "for", "what", "who", "when", "where", "how", "why",
        "a", "an", "and", "or", "but", "with", "from", "that", "this", "it", "on", "at", "by"
    }
    def tokenize(s):
        # Fjarlægja greinarmerki, skipta í orð, lágstafa, hunsa stopporð
        tokens = re.sub(r'[^\w\s]', '', s.lower()).split()
        return {t for t in tokens if t not in STOP_WORDS and len(t) > 1}
    q_tokens = tokenize(query)
    c_text = (citation.get("title", "") + " " + citation.get("snippet", ""))
    c_tokens = tokenize(c_text)
    if not q_tokens or not c_tokens:
        return 0.0
    intersection = q_tokens & c_tokens
    # Query coverage: hve margir query tokens finnast í citation
    # Jaccard er of strangur þegar citation text er langur
    coverage = len(intersection) / len(q_tokens) if q_tokens else 0.0
    return coverage

RELEVANCE_THRESHOLD = 0.15

def rrf_merge(source_groups: List[Dict], query: str, k: int = 60) -> List[Dict]:
    scores: Dict[str, dict] = {}
    for group in source_groups:
        source = group.get("source", "")
        base_w = SOURCE_WEIGHTS.get(source, 1.0)
        for citation in group.get("citations", []):
            # Sprint 82: Tier-aware weighting
            tier = citation.get("tier", "general")
            tier_mult = TIER_MULTIPLIERS.get(tier, 1.0)
            w = base_w * tier_mult
            if not citation.get("simhash"):
                title = citation.get("title", "") or ""
                snippet = citation.get("snippet", "") or ""
                citation["simhash"] = simhash_64(f"{title} {snippet}")
            url = citation.get("url", "")
            rank = citation.get("rank", 99)
            rrf = w * (1.0 / (k + rank))
            if url not in scores or scores[url]["rrf"] < rrf:
                scores[url] = {**citation, "rrf": rrf, "_weight": w}

    merged = sorted(scores.values(), key=lambda x: -x["rrf"])
    
    # Sprint 84: Relevance filter — sía út óviðkomandi heimildir
    # Þetta kemur í veg fyrir að "Hvað er klukkan í Tokyo?" fái
    # tilvitnanir úr Stjórnarráðinu.
    if merged:
        merged = [c for c in merged if
                  c.get("tier") in ("government", "academic") or
                  _relevance_score(query, c) >= RELEVANCE_THRESHOLD]
    for i, c in enumerate(merged, 1):
        c["rank"] = i
    return merged

async def search_web_multi(query: str, max_results: int = 5) -> Dict:
    # Phase D: BÍN-based query normalization
    normalized_query = await lemmatize_query_terms(query)

    # Keyra allar heimildir samtímis
    staan, stjornar, tidindi, mojeek, wayback, visindavefur, althingi, hagstofa = await asyncio.gather(
        fetch_staan(normalized_query, max_results),
        fetch_stjornarradid(normalized_query, 30),
        fetch_stjornartidindi(normalized_query, max_results),
        _fetch_mojeek(normalized_query, max_results),
        fetch_wayback_snapshots(normalized_query, max_results),
        fetch_visindavefur(normalized_query, max_results),
        fetch_althingi(normalized_query, max_results),
        fetch_hagstofa(normalized_query, max_results),
    )

    # Sameina með RRF
    merged = rrf_merge([staan, stjornar, tidindi, mojeek, wayback, visindavefur, althingi, hagstofa], query)
    merged = deduplicate(merged)
    merged = source_cap(merged, max_per_source=2)
    merged = merged[:max_results]
    md = render_markdown(merged)

    return {
        "citations": merged,
        "markdown": md,
        "raw_count": sum(g.get("raw_count", 0) for g in [staan, stjornar, tidindi, mojeek, wayback, visindavefur, althingi, hagstofa]),
        "source": "multi",
    }

if __name__ == "__main__":
    async def test():
        res = await search_web_multi("forsætisráðherra", max_results=5)
        print(res["markdown"])
        print(f"\nHeimildir: {len(res['citations'])}")
        sources = set(c.get("source") for c in res["citations"])
        print(f"Sources: {sources}")
    asyncio.run(test())
