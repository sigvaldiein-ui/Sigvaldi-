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

# Registry — tool name → tool instance
REGISTRY: dict[str, BaseTool] = {
    "search_law": SearchLawTool(),
    "summarize_doc": SummarizeDocTool(),
    "classify_doc": ClassifyDocTool(),
    "translate_text": TranslateTextTool(),
}


def get_tool(name: str) -> BaseTool | None:
    """Skilar tool fyrir gefið nafn. None ef ekki til."""
    return REGISTRY.get(name)


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
