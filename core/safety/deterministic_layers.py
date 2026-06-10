
"""Deterministic PII detection layers — regex + validators.
Allir finnendur skila (span_start, span_end, text, type, layer, confidence)."""

import re
from typing import List, Tuple, Optional

# -----------------------------------------------------------
# 1. SÍMAR
# -----------------------------------------------------------
SÍMI_PATTERNS = [
    # +354 899 1234, 00354-899-1234
    r'(?:\+354[\s\-]?\d{3}[\s\-.]?\d{4})',
    # 00354-899-1234
    r'(?:00354[\s\-]?\d{3}[\s\-.]?\d{4})',
    # (354) 899 1234
    r'(?:\(354\)[\s]?\d{3}[\s\-.]?\d{4})',
    # 899-1234, 899 1234, 8991234
    r'(?<!\d)(?:[58]\d{2}[\s\-.]?\d{4})(?!\d)',
]

def find_simar(text: str) -> List[Tuple[int, int, str]]:
    """Finna íslensk símanúmer."""
    found = []
    for pat in SÍMI_PATTERNS:
        for m in re.finditer(pat, text):
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 2. NETFÖNG
# -----------------------------------------------------------
NETFANG_PATTERNS = [
    # standard netfang
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    # [at] form
    r'\b[A-Za-z0-9._%+-]+\[at\][A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    # (at) form
    r'\b[A-Za-z0-9._%+-]+\(at\)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
]

def normalize_adversarial_email(text: str) -> str:
    """Breytir adversarial netföngum yfir í venjuleg."""
    t = text.replace("[at]", "@").replace("(at)", "@")
    t = re.sub(r'\(hjá\)', '@', t, flags=re.IGNORECASE)
    t = re.sub(r'\bpunkt\b', '.', t, flags=re.IGNORECASE)
    t = re.sub(r'\bhja\b', '@', t, flags=re.IGNORECASE)
    return t

def find_netfong(text: str) -> List[Tuple[int, int, str]]:
    """Finna netföng, líka adversarial form."""
    found = []
    normalized = normalize_adversarial_email(text)
    for pat in NETFANG_PATTERNS:
        for m in re.finditer(pat, normalized):
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 3. BANKAREIKNINGAR
# -----------------------------------------------------------
REIKNINGUR_PATTERNS = [
    # 0133-26-012345, 0133 26 012345
    r'\b\d{4}[\s\-./]?\d{2}[\s\-./]?\d{6}\b',
    # b. 0133 h. 26 r. 012345
    r'[bB]\s*[.:]\s*\d{4}\s+[hH]\s*[.:]\s*\d{2}\s+[rR]\s*[.:]\s*\d{6}',
    # Bnr. 0133-26-012345, Rkn: 0133.26.012345
    r'(?:[Rr](?:kn|eikn|eikningur|n)[\s.:]*)\d{4}[\s\-./]?\d{2}[\s\-./]?\d{6}',
    # Konto 0133-26-012345
    r'[Kk]onto[\s:]*\d{4}[\s\-./]?\d{2}[\s\-./]?\d{6}',
]

def find_reikningar(text: str) -> List[Tuple[int, int, str]]:
    """Finna bankareikninga."""
    found = []
    for pat in REIKNINGUR_PATTERNS:
        for m in re.finditer(pat, text):
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 4. IBAN
# -----------------------------------------------------------
IBAN_PATTERN = r'IS[\s\-]?\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{2}'

def find_iban(text: str) -> List[Tuple[int, int, str]]:
    """Finna íslensk IBAN númer."""
    found = []
    for m in re.finditer(IBAN_PATTERN, text, re.IGNORECASE):
        found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 5. KORTANÚMER
# -----------------------------------------------------------
KORT_PATTERN = r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'

def find_kort(text: str) -> List[Tuple[int, int, str]]:
    """Finna kreditkortanúmer."""
    found = []
    for m in re.finditer(KORT_PATTERN, text):
        digits = re.sub(r'\D', '', m.group())
        if len(digits) == 16:
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 6. IP TÖLUR
# -----------------------------------------------------------
IP_PATTERNS = [
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IPv4
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6 full
    r'\b(?:[0-9a-fA-F]{1,4}:){2,6}[0-9a-fA-F]{1,4}\b',  # IPv6 stutt
    r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b',  # MAC
]

def find_ip(text: str) -> List[Tuple[int, int, str]]:
    """Finna IP tölur og MAC vistföng."""
    found = []
    for pat in IP_PATTERNS:
        for m in re.finditer(pat, text):
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 7. BÍLNÚMER
# -----------------------------------------------------------
BILNUMER_PATTERN = r'\b[A-ZÞÆÖÁÉÍÓÚÝÐ]{2}[\s\-]?\d{2,3}[A-Z]?\b'

def find_bilnumer(text: str) -> List[Tuple[int, int, str]]:
    """Finna íslensk bílnúmer."""
    found = []
    for m in re.finditer(BILNUMER_PATTERN, text):
        found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# 8. HEIMILISFÖNG
# -----------------------------------------------------------
# Íslensk póstnúmer 101-902
POSTNUMER = set(str(i) for i in range(101, 903))
# Algengar götur (stór stafur + ending)
GATA_PATTERN = r'\b[A-ZÁÉÍÓÚÝÞÆÖ][a-záéíóúýðþæö]{2,}(?:gata|vegur|braut|stræti|stígur|torg|hólar|grund|bær|hjalli|melur|háls|móar|garðar|vellir|dalur|nes|eyri|vík)[\s]*\d{1,3}\b'

def find_heimilisfong(text: str) -> List[Tuple[int, int, str]]:
    """Finna heimilisföng (gata + númer + póstnúmer)."""
    found = []
    for m in re.finditer(GATA_PATTERN, text):
        end = m.end()
        # Leita að póstnúmeri á eftir
        rest = text[end:end+20]
        post_match = re.search(r'\b(\d{3})\b', rest)
        if post_match and post_match.group(1) in POSTNUMER:
            end = end + post_match.end()
            full = text[m.start():end]
            found.append((m.start(), end, full))
        else:
            found.append((m.start(), m.end(), m.group()))
    return dedupe_spans(found)

# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------
def dedupe_spans(spans: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    """Fjarlægja skarandi span, halda því lengsta."""
    if not spans:
        return []
    sorted_spans = sorted(spans, key=lambda x: (x[0], -(x[1]-x[0])))
    result = []
    for s in sorted_spans:
        if not result or s[0] >= result[-1][1]:
            result.append(s)
    return result
