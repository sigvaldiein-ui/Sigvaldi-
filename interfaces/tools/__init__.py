"""Sprint 97.6 — Capability Registry Recovery."""
from interfaces.tools.base import BaseTool
from interfaces.tools.search_law import SearchLawTool
from interfaces.tools.summarize_doc import SummarizeDocTool
from interfaces.tools.classify_doc import ClassifyDocTool
from interfaces.tools.translate_text import TranslateTextTool
from interfaces.tools.pdf_gen import Pdf_genTool
from interfaces.tools.api_exec import Api_execTool
from interfaces.tools.mail_send import Mail_sendTool

REGISTRY = {
    "search_law": SearchLawTool(),
    "summarize_doc": SummarizeDocTool(),
    "classify_doc": ClassifyDocTool(),
    "translate_text": TranslateTextTool(),
    "pdf_gen": Pdf_genTool(),
    "api_exec": Api_execTool(),
    "mail_send": Mail_sendTool(),
}

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
CRITICAL_TOOLS = {"mail_send", "api_exec", "pdf_gen"}  # Krefjast HITL samþykktar


def get_tool(name: str) -> BaseTool | None:
    """Pure registry lookup. NO tier check."""
    return REGISTRY.get(name)

def check_tier_for_tool(tool_name: str, user_tier: str) -> None:
    """Single source of tier truth at API boundary."""
    required = TIER_REQUIREMENTS.get(tool_name, "Vitinn")
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get(required, 0):
        from fastapi.exceptions import HTTPException
        raise HTTPException(status_code=403, detail=f"Tool '{tool_name}' requires tier {required}")

def list_tools() -> list[dict]:
    return [t.to_mcp_schema() for t in REGISTRY.values()]
