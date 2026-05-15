"""
Sprint 83 — PII Sentry v1 (Vörðurinn)
Greinir persónuupplýsingar og beinir fyrirspurn að Hvelfingunni.
Hannað af Aðal — soft-warn í V1, hard-route í V2.
"""
import re, logging

logger = logging.getLogger("alvitur.pii_sentry")

# ── PII Mynstur ─────────────────────────────────────────────

KT_PATTERN = re.compile(r'\b\d{6}-?\d{4}\b')           # Kennitala
PHONE_PATTERN = re.compile(r'\b\d{3}[\s-]?\d{4}\b')    # Símanúmer (einfalt)
EMAIL_PATTERN = re.compile(r'\b[\w.-]+@[\w.-]+\.\w{2,}\b')  # Tölvupóstur

# Íslensk eiginnöfn (algengustu) — stækkað í V2 með NLP
_ICELANDIC_FIRST_NAMES = {
    "jón", "guðrún", "sigríður", "ólafur", "helga", "magnús", "kristín",
    "einar", "anna", "pétur", "maría", "jóhann", "ragnar", "katrín",
    "sveinn", "valdís", "gunnar", "hanna", "björn", "lilja",
    "sigvaldi", "þorgerður", "inga", "daði", "eyjólfur", "alma",
    "kristrún", "logi", "þorbjörg", "jóhann", "ragnar"
}

# Algeng íslensk heimilisfangamynstur
_ADDRESS_PATTERN = re.compile(
    r'\b(?:Laugavegur|Hverfisgata|Skólavörðustígur|Bankastræti|'
    r'Austurstræti|Suðurlandsbraut|Borgartún|Ármúli|'
    r'Grensásvegur|Lágmúli|Skeifan|Höfðabakki)\s+\d+',
    re.IGNORECASE
)

def detect_pii(query: str) -> dict:
    """
    Skannar fyrirspurn fyrir persónuupplýsingum.
    
    Returns:
        dict með:
        - has_pii: bool
        - pii_types: list af fundnum tegundum
        - warning: skilaboð til notanda (eða tómur strengur)
        - should_route_to_vault: bool (alltaf False í V1 soft-warn)
    """
    result = {
        "has_pii": False,
        "pii_types": [],
        "warning": "",
        "should_route_to_vault": False  # V1: soft-warn aðeins
    }
    
    detected = []
    
    # Kennitala
    if KT_PATTERN.search(query):
        detected.append("kennitala")
        result["has_pii"] = True
    
    # Símanúmer
    if PHONE_PATTERN.search(query):
        detected.append("símanúmer")
        result["has_pii"] = True
    
    # Tölvupóstur
    if EMAIL_PATTERN.search(query):
        detected.append("tölvupóstur")
        result["has_pii"] = True
    
    # Íslensk eiginnöfn (einföld leit)
    query_lower = query.lower()
    for name in _ICELANDIC_FIRST_NAMES:
        if re.search(r'\b' + re.escape(name) + r'\b', query_lower):
            detected.append("nafn")
            result["has_pii"] = True
            break  # Eitt nafn nægir
    
    # Heimilisfang
    if _ADDRESS_PATTERN.search(query):
        detected.append("heimilisfang")
        result["has_pii"] = True
    
    result["pii_types"] = list(set(detected))
    
    if result["has_pii"]:
        result["warning"] = (
            "🔒 **Athugið:** Fyrirspurnin þín virðist innihalda persónuupplýsingar "
            f"({', '.join(result['pii_types'])}). Mælt er með að nota **Hvelfinguna** "
            "fyrir fullkomið trúnaðaröryggi — engin gögn fara út fyrir vélina."
        )
        logger.info(f"PII Sentry: fann {result['pii_types']}")
    
    return result


def strip_pii_for_search(query: str) -> str:
    """Fjarlægir PII úr fyrirspurn fyrir ytri leit."""
    sanitized = query
    sanitized = KT_PATTERN.sub('[KT]', sanitized)
    sanitized = EMAIL_PATTERN.sub('[tölvupóstur]', sanitized)
    sanitized = PHONE_PATTERN.sub('[sími]', sanitized)
    return sanitized
