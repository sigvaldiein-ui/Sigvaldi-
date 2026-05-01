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
