# interfaces/tools/base.py
"""
Sprint 57 — Abstract base class fyrir öll tools.

Tools eru MCP-ready þynnra lag yfir Skills.
Sérhvert tool skilgreinir:
  - name: strengur (t.d. "search_law")
  - description: lýsing fyrir MCP registry
  - run(**kwargs): async aðal fall
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class fyrir Alvitur tools — MCP-ready."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool nafn — t.d. 'search_law', 'summarize_doc'."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Lýsing á tool — notuð í MCP registry."""
        ...

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """
        Keyrir tool með gefnum arguments.
        Graceful degradation: ef villa kemur upp skal skila fallback gildi.
        """
        ...

    def to_mcp_schema(self) -> dict:
        """Skilar MCP-samhæfu schema fyrir þetta tool."""
        return {
            "name": self.name,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return f"<Tool name={self.name}>"

# ── Sprint 101: Output Filter ─────────────────────────────────────────────
PER_TIER_SCHEMAS = {
    "api_exec": {"Vitinn": ["status"], "Hvelfingin": ["status", "url"], "Starfsmaður": ["status", "url", "domain"]},
    "mail_send": {"Vitinn": ["status"], "Hvelfingin": ["status", "to"], "Starfsmaður": ["status", "to", "subject", "audit_hash"]},
    "search_law": {"Vitinn": ["documents"], "Hvelfingin": ["documents", "count"], "Starfsmaður": ["documents", "count"]},
    "pdf_gen": {"Vitinn": ["status"], "Hvelfingin": ["status", "filename"], "Starfsmaður": ["status", "filename"]},
    "classify_doc": {"Vitinn": ["domain"], "Hvelfingin": ["domain", "confidence"], "Starfsmaður": ["domain", "confidence"]},
    "summarize_doc": {"Vitinn": ["summary"], "Hvelfingin": ["summary", "length"], "Starfsmaður": ["summary", "length"]},
    "translate_text": {"Vitinn": ["translated"], "Hvelfingin": ["translated", "source_lang"], "Starfsmaður": ["translated", "source_lang"]},
}

def sanitize_tool_output(tool_name: str, output_data, user_tier: str = "Vitinn"):
    """ADR-012: Per-tier per-tool output filter."""
    if not isinstance(output_data, dict):
        return {"error": "Invalid output format"}
    allowed_keys = PER_TIER_SCHEMAS.get(tool_name, {}).get(user_tier, [])
    sanitized = {k: v for k, v in output_data.items() if k in allowed_keys}
    if not sanitized and output_data:
        return {"status": "filtered_by_policy", "message": "Data stripped per tier compliance"}
    return sanitized

def sanitize_tool_output(tool_name: str, output_data):
    """ADR-010: Pro-Mode Output Filter. Strict Whitelist — algjört minnisleysi."""
    if not isinstance(output_data, dict):
        return {"error": "Invalid output format — dropped for safety"}
    allowed_keys = ALLOWED_OUTPUT_SCHEMAS.get(tool_name, [])
    sanitized = {k: v for k, v in output_data.items() if k in allowed_keys}
    if not sanitized and output_data:
        from interfaces.tools.audit_logger import SecureAuditLogger
        logger = SecureAuditLogger()
        logger.last_hash = "0" * 64  # Nota instance ef til, annars nýjan
        logger.log_action("SYSTEM", "CORE", tool_name, "CRITICAL_SCHEMA_DRIFT")
        return {
            "status": "circuit_breaker_triggered",
            "error": "Kerfisvilla: Ytri gagnaþjónusta svaraði ekki á stöðluðu formi. Beiðni skráð hjá kerfisstjórn."
        }
    return sanitized
