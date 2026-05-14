"""
Sprint 80c v2 — Heimildagátt (Source Gate)
Deterministic validation að LLM svar byggi á heimildum.
Notar stofnaleit (fyrstu 5 stafir) til að höndla íslenska fallbeygingu.
"""
import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger("alvitur.source_gate")

MAX_RETRIES = 2


def _extract_names(text: str) -> set:
    """Dregur út öll sérnöfn (hástafanafn + eftirnafn) úr texta."""
    if not text:
        return set()
    matches = re.findall(r"\b([A-ZÁÉÍÓÚÝÞÆÖÐ][a-záéíóúýþæðö]+(?: [A-ZÁÉÍÓÚÝÞÆÖÐ][a-záéíóúýþæðö]+)?)", text)
    return set(matches)


def _name_root(name: str) -> str:
    """Skilar fyrstu 5 stöfum í lágstöfum sem stofn fyrir íslenska fallbeygingu."""
    return name.split()[0][:5].lower() if name and name[0].isupper() else ""


def _names_in_rag(name_root_set: set, rag: str) -> bool:
    """Athugar hvort allir nafnstofnar finnist í RAG heimildum."""
    if not name_root_set or not rag:
        return False
    rag_lower = rag.lower()
    for root in name_root_set:
        if root not in rag_lower:
            return False
    return True


def _rag_contains_names(rag: str) -> bool:
    """Athugar hvort RAG innihaldi yfirleitt nein sérnöfn."""
    if not rag:
        return False
    return bool(re.findall(r"\b[A-ZÁÉÍÓÚÝÞÆÖÐ][a-záéíóúýþæðö]+ [A-ZÁÉÍÓÚÝÞÆÖÐ][a-záéíóúýþæðö]+", rag))


def _build_strict_prompt(query: str, file_context: str, enriched_rag: str, now_str: str, attempt: int) -> str:
    """Byggir strangara prompt fyrir 2. tilraun."""
    if attempt == 1:
        instruction = (
            "ÞÚ MÁTT AÐEINS nota nöfn og staðreyndir sem koma BEINT fram í HEIMILDIR hér að ofan. "
            "Ekki nota neinar upplýsingar úr þjálfunargögnum þínum. "
            "Ef nafn ráðherra kemur EKKI fram í HEIMILDUM, segðu þá: „Ég fann ekki nafnið í heimildum.“\n"
            "Svaraðu aftur, með þessum takmörkunum."
        )
    else:
        instruction = (
            "ÞETTA ER SÍÐASTA TILRAUN. Þú mátt EKKERT skálda. "
            "Afritaðu nafnið ORÐRÉTT úr HEIMILDUM. "
            "Ef það er ekki í HEIMILDUM, svaraðu NÁKVÆMLEGA: „Engar traustar heimildir fundust.“"
        )
    return (
        f"Þú ert Alvitur, íslenskur sérfræðingur.\n"
        f"Dagsetning: {now_str}\n\n"
        f"=== HEIMILDIR (RAUNTÍMAGÖGN) ===\n"
        f"{enriched_rag}{file_context}\n"
        f"=== ENDIR HEIMILDA ===\n\n"
        f"{instruction}\n\n"
        f"SPURNING NOTANDANS: {query}"
    )


async def validate_and_retry(
    query: str,
    file_context: str,
    enriched_rag: str,
    now_str: str,
    content: Optional[str],
    call_fn,
) -> Tuple[Optional[str], str]:
    """
    Heimildagátt með sjálfleiðréttingarlykkju.
    Núverandi stilling: Óvirkjuð — allt fer í gegn.
    Fært til Sprint 82 fyrir Glass-box arkitektúr.
    """
    # Gátt óvirkjuð fyrir Leið A — fært til Sprint 82
    return (content, "source_gate_bypass_sprint82")


def _extract_names_test():
    """Standalone empirical prófun."""
    cases = [
        ("Daði Már Kristófersson er ráðherra.", {"Daði Már Kristófersson"}),
        ("Hjörtur Árnason og Ívar Þórðarson.", {"Hjörtur Árnason", "Ívar Þórðarson"}),
        ("Engin sérnöfn hér.", set()),
        ("Þorgerður Katrín Gunnarsdóttir", {"Þorgerður Katrín Gunnarsdóttir"}),
    ]
    for text, expected in cases:
        result = _extract_names(text)
        ok = "OK" if result == expected else f"FAIL (fékk {result})"
        print(f"{ok}: {text[:50]}")


if __name__ == "__main__":
    _extract_names_test()
    print("\n_name_root próf:")
    for name, expected_root in [
        ("Daði Már", "daði"),
        ("Daða Má", "daða"),
        ("Kristrún Frostadóttir", "krist"),
        ("Alvitur", ""),
    ]:
        root = _name_root(name)
        ok = "OK" if root == expected_root else f"FAIL (fékk {root})"
        print(f"{ok}: {name} -> {root}")
