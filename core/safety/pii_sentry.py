
"""PII Sentry — aðal-API fyrir persónuverndarvörn.

Notkun:
    from core.safety.pii_sentry import scrub
    result = scrub(text)
    if result.blocked:
        return "Útsending stöðvuð — mögulegar persónuupplýsingar"
    print(result.scrubbed)  # hreinsaður texti
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple

from core.safety.normalize import digit_runs, wordnums_to_digits
from core.safety.validators import kt_valid, kt_is_company, luhn_valid, iban_is_valid
from core.safety.deterministic_layers import (
    find_simar, find_netfong, find_reikningar,
    find_iban, find_kort, find_ip, find_bilnumer, find_heimilisfong
)
from core.safety.gazetteer import find_nofn_gazetteer
from core.safety.ner_client import find_nofn_ner

@dataclass
class Finding:
    span: Tuple[int, int]
    text: str
    type: str          # kt, simi, netfang, reikningur, kort, iban, nafn, heimilisfang, bilnumer, ip, ovisst
    layer: str         # regex, validator, gazetteer, ner, failclosed
    confidence: float = 1.0

@dataclass
class ScrubResult:
    original: str
    scrubbed: str
    findings: List[Finding] = field(default_factory=list)
    blocked: bool = False

TYPE_LABELS = {
    "kt": "[KT]", "simi": "[SÍMI]", "netfang": "[NETFANG]",
    "reikningur": "[REIKNINGUR]", "kort": "[KORT]", "iban": "[IBAN]",
    "nafn": "[NAFN]", "heimilisfang": "[HEIMILISFANG]",
    "bilnumer": "[BÍLNÚMER]", "ip": "[IP]", "ovisst": "[ÓVÍST]"
}

SUSPICIOUS = [
    (r'\b\d{6}\b', "6 stafa runa — gæti verið hluti af kennitölu"),
    (r'(kennitala|kt\.?|ssn)', "PII-orð án matchaðs PII"),
    (r'[A-Za-z0-9+/]{16,}={0,2}', "base64-líklegt"),
]

def scrub(text: str) -> ScrubResult:
    """Aðal-API: skilar hreinsuðum texta og lista yfir fundin PII."""
    findings = []

    # Lag 1: Deterministic — regex + validators
    findings += _kt_layer(text)
    findings += _regex_layer(text)

    # Lag 2: Gazetteer (nöfn)
    findings += _gazetteer_layer(text)

    # Lag 3: NER (stub — engin áhrif enn)
    findings += _ner_layer(text)

    # Lag 4: Fail-closed
    findings += _failclosed_layer(text, findings)

    # Dedupe + redact
    findings = _dedupe(findings)
    scrubbed = _redact(text, findings)

    # Blokka ef of mörg óviss atriði
    ovisst_count = sum(1 for f in findings if f.type == "ovisst")
    blocked = ovisst_count > 3

    return ScrubResult(
        original=text,
        scrubbed=scrubbed,
        findings=findings,
        blocked=blocked
    )

def _kt_layer(text: str) -> List[Finding]:
    """Finna kennitölur með vartöluprófi."""
    findings = []
    normalized = wordnums_to_digits(text)
    runs = digit_runs(normalized)
    seen = set()
    for digits, offsets in runs:
        for i in range(len(digits) - 9):
            cand = digits[i:i+10]
            if cand in seen:
                continue
            seen.add(cand)
            if kt_valid(cand):
                if kt_is_company(cand):
                    continue  # fyrirtækja-kt = í gegn
                findings.append(Finding(
                    span=(offsets[i], offsets[i+9]+1),
                    text=cand,
                    type="kt",
                    layer="validator",
                    confidence=1.0
                ))
    return findings

def _regex_layer(text: str) -> List[Finding]:
    """Öll regex/validator lögin í einu."""
    findings = []
    for start, end, match in find_simar(text):
        findings.append(Finding((start, end), match, "simi", "regex", 1.0))
    for start, end, match in find_netfong(text):
        findings.append(Finding((start, end), match, "netfang", "regex", 1.0))
    for start, end, match in find_reikningar(text):
        findings.append(Finding((start, end), match, "reikningur", "regex", 1.0))
    for start, end, match in find_iban(text):
        digits = re.sub(r'\D', '', match)
        if iban_is_valid(digits):
            findings.append(Finding((start, end), match, "iban", "validator", 1.0))
    for start, end, match in find_kort(text):
        digits = re.sub(r'\D', '', match)
        if luhn_valid(digits):
            findings.append(Finding((start, end), match, "kort", "validator", 1.0))
    for start, end, match in find_ip(text):
        findings.append(Finding((start, end), match, "ip", "regex", 1.0))
    for start, end, match in find_bilnumer(text):
        findings.append(Finding((start, end), match, "bilnumer", "regex", 1.0))
    for start, end, match in find_heimilisfong(text):
        findings.append(Finding((start, end), match, "heimilisfang", "regex", 1.0))
    # PII-fix: finna kennitölur með bandstriki/bili — DDMMYY[- ]?NNNN
    kt_regex = re.compile(r"\b(\d{6})[- ]?(\d{4})\b")
    for m in kt_regex.finditer(text):
        findings.append(Finding((m.start(), m.end()), m.group(), "kt", "regex", 0.95))
    return findings

def _gazetteer_layer(text: str) -> List[Finding]:
    """Finna nöfn með gazetteer."""
    findings = []
    for start, end, match in find_nofn_gazetteer(text):
        findings.append(Finding((start, end), match, "nafn", "gazetteer", 0.9))
    return findings

def _ner_layer(text: str) -> List[Finding]:
    """Finna nöfn með NER."""
    findings = []
    for start, end, match in find_nofn_ner(text):
        findings.append(Finding((start, end), match, "nafn", "ner", 0.85))
    return findings

def _failclosed_layer(text: str, existing: List[Finding]) -> List[Finding]:
    """Finna grunsamleg mynstur sem ekkert lag náði að staðfesta."""
    findings = []
    for pat, reason in SUSPICIOUS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            # Athuga hvort þetta skarist við existing
            overlap = False
            for f in existing:
                if m.start() < f.span[1] and m.end() > f.span[0]:
                    overlap = True
                    break
            if not overlap:
                findings.append(Finding(
                    (m.start(), m.end()),
                    m.group(),
                    "ovisst",
                    "failclosed",
                    0.5
                ))
    return findings

def _dedupe(findings: List[Finding]) -> List[Finding]:
    """Fjarlægja skarandi span — halda því með hæsta confidence."""
    if not findings:
        return []
    sorted_f = sorted(findings, key=lambda f: (f.span[0], -(f.span[1]-f.span[0])))
    result = []
    for f in sorted_f:
        if not result or f.span[0] >= result[-1].span[1]:
            result.append(f)
    return result

def _redact(text: str, findings: List[Finding]) -> str:
    """Skipta PII út fyrir merki. Vinnur aftast-fyrst til að varðveita offset."""
    for f in sorted(findings, key=lambda x: x.span[0], reverse=True):
        label = TYPE_LABELS.get(f.type, "[???]")
        text = text[:f.span[0]] + label + text[f.span[1]:]
    return text
