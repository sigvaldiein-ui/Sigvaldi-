# interfaces/tools/classify_doc.py
"""
Sprint 57 — ClassifyDocTool.
Þynnra lag yfir ClassifySkill — MCP-ready.
"""
import logging
from interfaces.tools.base import BaseTool
from interfaces.skills.classify import ClassifySkill

logger = logging.getLogger("alvitur.web")

_classify_skill = ClassifySkill()


class ClassifyDocTool(BaseTool):
    """Flokkar texta í domain: legal, finance, writing, research, general."""

    @property
    def name(self) -> str:
        return "classify_doc"

    @property
    def description(self) -> str:
        return (
            "Flokkar texta í eitt af fimm domains: legal, finance, writing, research, general. "
            "Nota þegar þarf að vita hvers konar texti er á undan frekari vinnslu."
        )

    async def run(self, text: str = "") -> str:
        """
        kwargs:
          text: inntakstexti
        Skilar: domain strengur
        """
        return await _classify_skill.run(text=text)
