# interfaces/tools/__init__.py
"""
Sprint 57 — Tools package (MCP-ready).

Tools eru þynnra lag yfir Skills, hannað fyrir MCP integration.
Sérhvert tool er kallanlegt með name, description og run().

Tiltæk tools:
  SearchLawTool    — leita í igc_law_pilot RAG
  SummarizeDocTool — texta samantekt (via SummarizeSkill)
  ClassifyDocTool  — domain flokkun (via ClassifySkill)
  TranslateTextTool — íslenska þýðing (via TranslateSkill)
"""
from interfaces.tools.base import BaseTool
from interfaces.tools.search_law import SearchLawTool
from interfaces.tools.summarize_doc import SummarizeDocTool
from interfaces.tools.classify_doc import ClassifyDocTool
from interfaces.tools.translate_text import TranslateTextTool
from interfaces.tools.pdf_gen import Pdf_genTool
from interfaces.tools.api_exec import Api_execTool
from interfaces.tools.mail_send import Mail_sendTool

# Registry — tool name → tool instance
REGISTRY: dict[str, BaseTool] = {
    "search_law": SearchLawTool(),
    "summarize_doc": SummarizeDocTool(),
    "classify_doc": ClassifyDocTool(),
    "translate_text": TranslateTextTool(),
    "pdf_gen": Pdf_genTool(),
    "api_exec": Api_execTool(),
    "mail_send": Mail_sendTool(),
}


# ── ADR-008: Capability Registry ──────────────────────────────────────────
TIER_REQUIREMENTS = {
    "search_law": "Vitinn",
    "summarize_doc": "Vitinn",
    "classify_doc": "Vitinn",
    "translate_text": "Vitinn",
    "pdf_gen": "Hvelfingin",
    "api_exec": "Starfsmaður",
    "mail_send": "Starfsmaður",
}

TIER_LEVELS = {"Vitinn": 0, "Hvelfingin": 1, "Starfsmaður": 2}


def get_tool(name: str, user_tier: str = "Vitinn") -> BaseTool | None:
    """ADR-008: Skilar tool ef user_tier uppfyllir kröfur. None annars."""
    tool = REGISTRY.get(name)
    if not tool:
        return None
    required = TIER_REQUIREMENTS.get(name, "Vitinn")
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get(required, 0):
        from fastapi.exceptions import HTTPException
        raise HTTPException(status_code=403, detail=f"Tool '{name}' requires tier {required}")
    return tool


def list_tools() -> list[dict]:
    """Skilar MCP-samhæfum lista af öllum tools."""
    return [t.to_mcp_schema() for t in REGISTRY.values()]


__all__ = [
    "BaseTool",
    "SearchLawTool",
    "SummarizeDocTool",
    "ClassifyDocTool",
    "TranslateTextTool",
    "REGISTRY",
    "get_tool",
    "list_tools",
]
