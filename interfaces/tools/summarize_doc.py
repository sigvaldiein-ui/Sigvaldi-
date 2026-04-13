# interfaces/tools/summarize_doc.py
"""
Sprint 57 — SummarizeDocTool.
Þynnra lag yfir SummarizeSkill — MCP-ready.
"""
import logging
from interfaces.tools.base import BaseTool
from interfaces.skills.summarize import SummarizeSkill

logger = logging.getLogger("alvitur.web")

_summarize_skill = SummarizeSkill()


class SummarizeDocTool(BaseTool):
    """Dregur saman texta eða skjal í 3-5 setningar á íslensku."""

    @property
    def name(self) -> str:
        return "summarize_doc"

    @property
    def description(self) -> str:
        return (
            "Dregur saman texta eða skjal í 3-5 setningar á íslensku. "
            "Nota þegar notandi biður um samantekt á löngu skjali eða texta."
        )

    async def run(self, text: str = "", tier: str = "general") -> str:
        """
        kwargs:
          text: inntakstexti
          tier: 'general' eða 'vault'
        Skilar: samantekt á íslensku
        """
        return await _summarize_skill.run(text=text, tier=tier)
