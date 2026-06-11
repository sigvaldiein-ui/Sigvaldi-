"""Erindrekinn — Tólaskrá (innri tól).

Öll tól sem Erindrekinn getur kallað á.
Núna eru þetta aðeins dummy-útfærslur.
"""


def tool_draft_document(topic: str, context: str = "") -> str:
    """Semur drög að skjali.

    Í framtíðinni mun þetta kalla á LLM.
    """
    print(f"[TÓL] Sem drög að skjali um: {topic}")
    return f"DRAFT: Skjal um {topic} (dummy)".upper()


def tool_analyze_text(text: str) -> str:
    """Greinir texta — dregur út lykilatriði.

    Í framtíðinni mun þetta kalla á LLM.
    """
    print(f"[TÓL] Greini texta: {text[:50]}...")
    word_count = len(text.split())
    return f"Greining: {word_count} orð, lykilatriði: [dummy]"


def tool_write_code(spec: str) -> str:
    """Skrifar kóða út frá lýsingu.

    Í framtíðinni mun þetta keyra í sandkassa.
    """
    print(f"[TÓL] Skrifa kóða fyrir: {spec}")
    return "def hello():\n    return 'Hello from Erindrekinn!'"


def tool_research(query: str) -> str:
    """Rannsakar efni — kallar á Vitann.

    Í framtíðinni mun þetta kalla á Vitann í gegnum API.
    """
    print(f"[TÓL] Rannsaka: {query}")
    return f"Rannsóknarniðurstöður fyrir '{query}': [dummy — kalla á Vitann]"


# ─── Tólaskrá (registry) ───
AVAILABLE_TOOLS = {
    "draft_document": tool_draft_document,
    "analyze_text": tool_analyze_text,
    "write_code": tool_write_code,
    "research": tool_research,
}


def get_tool(name: str):
    """Sækir tól eftir nafni."""
    return AVAILABLE_TOOLS.get(name)


# ─── Keyrslu-dæmi ───
if __name__ == "__main__":
    print("=== Tiltæk tól ===")
    for name, func in AVAILABLE_TOOLS.items():
        print(f"  {name}: {func.__doc__.strip().split(chr(10))[0]}")
