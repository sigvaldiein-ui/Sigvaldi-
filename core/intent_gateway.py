"""
Sprint 64 Track B1 — Intent Gateway (rule-based classifier).

Ráðsamþykkt: 80% accuracy á millisekúndum, ekki 95% á sekúndu.
Engin LLM-call í fyrstu umferð (kemur í Sprint 65 þegar confidence < 0.6).

Heuristics (samanlagt):
1. File signal: extension / content-type → source_hint + adapter_hint
2. Tier signal: X-Alvitur-Tier=vault → sensitivity=high
3. Keyword signals: domain (legal/financial/technical/public/general)
4. Length signal: long query/file → reasoning_depth=deep
5. Confidence: fall af merkjafjölda + styrk

Skilar ónæmanlegu (frozen) IntentResult frá models/intent.py.
"""

from __future__ import annotations

import re
from typing import Optional

from models.intent import IntentResult, Domain, ReasoningDepth, SourceHint
from core.intent_llm_fallback import refine_with_llm

# ── Lykilorðalistar (lower-case, ekki case-sensitive) ─────────────────────
_KW_LEGAL = {
    "samningur", "samning", "lög", "löggjöf", "reglugerð", "reglugerðar",
    "dómur", "dómstól", "málsókn", "kröfu", "krafa", "höfundarréttar",
    "persónuvernd", "gdpr", "ákvæði", "skilmál",
}
_KW_FINANCIAL = {
    "reikning", "reikningur", "hagnað", "tap", "vsk", "skatt", "skattur",
    "isk", "eur", "usd", "fjárhag", "bókhald", "tekjur", "kostnað",
    "arðgreiðsl", "fjárfest", "lán", "vextir", "greiðsl",
}
_KW_TECHNICAL = {
    "kóði", "python", "javascript", "api", "error", "exception",
    "docker", "kubernetes", "git", "bash", "sql", "bug", "stack trace",
    "traceback", "endpoint", "json", "http",
}
_KW_PUBLIC = {
    # Institutions (original S64 set)
    "ráðuneyti", "stofnun", "opinber", "ríki", "sveitarfélag",
    "alþingi", "forseti", "landsréttur", "hæstirétt",
    # Citizen services — ID documents
    "ökuskírtein", "vegabréf", "nafnskírtein", "kennitala",
    "sakavottorð", "búsetuvottorð",
    # Tax & benefits administration (citizen-facing)
    "rsk", "skatturinn", "skattframtal", "skattskýrsl", "skattkort",
    "staðgreiðsla",
    "fæðingarorlof", "fæðingarstyrk", "barnabæt", "vaxtabæt",
    "atvinnuleysisbæt", "örorkubæt", "ellilífeyri",
    # Agencies
    "sjúkratrygging", "þjóðskrá", "lögheimil",
    "vmst", "vinnumálastofnun", "tryggingastofnun",
    "umferðarstofa", "samgöngustofa",
    # Digital gov
    "ísland.is", "island.is", "mínar síður", "rafræn skilríki",
    "auðkenni",
    # Common service verbs
    "umsókn", "eyðublað", "leikskól", "grunnskól",
}

# ── Depth-keyword listar (S68 A.2) ──────────────────────────────────────
# Semantic signals fyrir reasoning_depth. Precedence í depth-block neðar.
# Stem-based (Lesson #19 frá S67).
_KW_DEPTH_STANDARD = {
    # explanatory verbs (require 1-2 paragraph answer)
    "útskýr", "skýr",                    # útskýra, útskýrðu, skýring
    "hvernig",                           # how-to (soft signal)
    "af hverju", "hvers vegna",          # causal
    "hvað er", "hvað eru",               # definitional
    "hvaða",                             # ranking/selection (accept FP trade-off
                                         # on "hvaða dagsetning er í dag")
    "berðu saman", "samanburð",          # comparison
}

_KW_DEPTH_DEEP = {
    # analysis verbs (explicit)
    "greina", "greindu", "greining",
    # conditional / hypothetical (space-wrapped to avoid substring FP)
    " ef ",
    # multi-party legal
    "réttindi", "skyldur", "krefja",
    # long-range synthesis cue (hard)
    "í smáatriðum", "smáatriðum", "i smaatridum", "smaatridum",
    # multi-step setup
    "set ég upp", "set upp", "uppsetning",
}

# "saga"/"sögu" require co-occurrence (Opus suggestion 1)
_KW_DEPTH_DEEP_SAGA_GUARDED = {"saga", "sögu", "sogu"}
_KW_DEPTH_DEEP_SAGA_COUES  = {"í smáatriðum", "smáatriðum", "smaatridum",
                              "segðu mér", "segdu mer"}

# "virkar" requires "hvernig" co-occurrence (Opus suggestion 2)
_KW_DEPTH_DEEP_MECH_TRIGGER = "virkar"
_KW_DEPTH_DEEP_MECH_GUARD   = "hvernig"


# ── File extension → (source_hint, adapter_hint, has_tabular) ─────────────
_EXT_MAP: dict[str, tuple[SourceHint, str]] = {
    "xlsx": ("xlsx", "tabular"),
    "xls":  ("xlsx", "tabular"),
    "csv":  ("xlsx", "tabular"),
    "pdf":  ("pdf",  "rag"),
    "docx": ("docx", "rag"),
    "doc":  ("docx", "rag"),
    "txt":  ("text", "rag"),
    "png":  ("image", "vision"),
    "jpg":  ("image", "vision"),
    "jpeg": ("image", "vision"),
    "mp3":  ("audio", "whisper"),
    "wav":  ("audio", "whisper"),
    "m4a":  ("audio", "whisper"),
}

_NUMBER_RE = re.compile(r"\d[\d.,]*\s*(%|kr|isk|eur|usd)?", re.IGNORECASE)


def _ext_of(filename: Optional[str]) -> Optional[str]:
    if not filename or "." not in filename:
        return None
    return filename.rsplit(".", 1)[1].lower()


def _score_keywords(query_lower: str) -> tuple[Domain, int]:
    """Finn sterkasta domain match + fjölda hits (fyrir confidence).

    Tie-break priority (S67-B): public > legal > technical > financial.
    Citizen-services queries ("RSK skattskýrslu") oft match bæði
    public (rsk, skattskýrsla) og financial (skatt, kostnað).
    Public vinnur alltaf þegar hits eru jöfn.
    """
    hits = {
        "legal":     sum(1 for kw in _KW_LEGAL     if kw in query_lower),
        "financial": sum(1 for kw in _KW_FINANCIAL if kw in query_lower),
        "technical": sum(1 for kw in _KW_TECHNICAL if kw in query_lower),
        "public":    sum(1 for kw in _KW_PUBLIC    if kw in query_lower),
    }
    # Sort by (hit_count DESC, priority DESC). Higher priority wins ties.
    priority = {"public": 4, "legal": 3, "technical": 2, "financial": 1}
    best_domain = max(hits, key=lambda d: (hits[d], priority[d]))
    best_count = hits[best_domain]
    if best_count == 0:
        return "general", 0
    return best_domain, best_count  # type: ignore


def classify_intent(
    query: Optional[str] = None,
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    tier: Optional[str] = None,
) -> IntentResult:
    """
    Rule-based intent classification.

    Args:
        query: Texti frá notanda (getur verið tómt ef hrein skráarupphleðsla)
        filename: Nafn á upploaded file (kemur úr UploadFile.filename)
        file_size: Stærð í bytes (fyrir depth heuristic)
        tier: X-Alvitur-Tier header ('vault' → sensitivity=high)

    Returns:
        Frozen IntentResult skv. models/intent.py skema.
    """
    q = (query or "").strip()
    q_lower = q.lower()
    ext = _ext_of(filename)

    # ── 1. File signal ──
    source_hint: Optional[SourceHint] = None
    adapter_hint: Optional[str] = None
    if ext and ext in _EXT_MAP:
        source_hint, adapter_hint = _EXT_MAP[ext]
    elif q:
        source_hint = "text"

    # ── 2. Tier signal ──
    sensitivity = "high" if (tier or "").lower() == "vault" else "low"

    # ── 3. Domain keywords ──
    kw_domain, kw_count = _score_keywords(q_lower)
    domain: Domain = kw_domain

    # Financial nudge: mörg númer+gjaldmiðilsmerki → financial boost
    num_hits = len(_NUMBER_RE.findall(q_lower))
    if domain == "general" and num_hits >= 3:
        domain = "financial"
        kw_count = max(kw_count, 1)

    # File-based domain override (veikari en skýr keyword match)
    if domain == "general" and adapter_hint == "tabular":
        domain = "financial"  # xlsx án keywords → líklegast fjárhagsleg tafla

    # ── 4. Reasoning depth ──
    #
    # Precedence (highest wins). Changed in S68 A.2:
    # length is now a signal, not a gate.
    #   1. Hard size limits           -> deep   (keep: long input always deep)
    #   2. DEEP keyword match         -> deep   (semantic override)
    #   3. STANDARD keyword match     -> standard
    #   4. Length < 80 and no file    -> fast   (fallback, was gate)
    #   5. Default                    -> standard (finally reachable)
    #
    # When both DEEP and STANDARD match, DEEP wins (analysis dominates
    # explanation). Documented trade-off: "hvaða X er í dag?" may route
    # standard; accepted until A.3 eval shows actual impact.
    reasoning_depth: ReasoningDepth = "standard"
    total_chars = len(q) + (file_size or 0) // 4  # grófur token-proxy

    # (1) hard size
    if total_chars > 5000 or (file_size or 0) > 100_000:
        reasoning_depth = "deep"
    else:
        # (2) DEEP keywords (with safety gates)
        deep_hit = any(kw in q_lower for kw in _KW_DEPTH_DEEP)

        # saga/sögu guard: require co-occurrence with depth cue
        if not deep_hit and any(kw in q_lower for kw in _KW_DEPTH_DEEP_SAGA_GUARDED):
            if (any(cue in q_lower for cue in _KW_DEPTH_DEEP_SAGA_COUES)
                    or total_chars > 60):
                deep_hit = True

        # virkar guard: require "hvernig" in same query
        if not deep_hit and _KW_DEPTH_DEEP_MECH_TRIGGER in q_lower:
            if _KW_DEPTH_DEEP_MECH_GUARD in q_lower:
                deep_hit = True

        if deep_hit:
            reasoning_depth = "deep"
        # (3) STANDARD keywords
        elif any(kw in q_lower for kw in _KW_DEPTH_STANDARD):
            reasoning_depth = "standard"
        # (4) length fast fallback
        elif total_chars < 80 and not filename:
            reasoning_depth = "fast"
        # (5) default is already "standard"

    # ── 5. Confidence ──
    # Base 0.5; +0.15 per strong signal, cap 0.95
    confidence = 0.5
    if kw_count >= 2:
        confidence += 0.30
    elif kw_count == 1:
        confidence += 0.15
    if ext and ext in _EXT_MAP:
        confidence += 0.15
    if sensitivity == "high":
        confidence += 0.05
    if num_hits >= 3 and domain == "financial":
        confidence += 0.10
    confidence = min(confidence, 0.95)

    # Ef ekkert merki yfirhöfuð → lágt conf (triggers LLM fallback í S65)
    if kw_count == 0 and not ext and total_chars < 20:
        confidence = 0.45

    _rule_result = IntentResult(
        domain=domain,
        reasoning_depth=reasoning_depth,
        adapter_hint=adapter_hint,
        confidence_score=round(confidence, 2),
        sensitivity=sensitivity,  # type: ignore
        source_hint=source_hint,
    )
    return refine_with_llm(query, filename, file_size, _rule_result)
