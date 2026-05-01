# interfaces/tools/translate_text.py
"""
Sprint 57 — TranslateTextTool.
Þynnra lag yfir TranslateSkill — MCP-ready.
"""
import logging
from interfaces.tools.base import BaseTool
from interfaces.skills.translate import TranslateSkill

logger = logging.getLogger("alvitur.web")

_translate_skill = TranslateSkill()


class TranslateTextTool(BaseTool):
    """Þýðir texta yfir á fallega, náttúrulega íslensku."""

    @property
    def name(self) -> str:
        return "translate_text"

    @property
    def description(self) -> str:
        return (
            "Þýðir texta á hvaða tungumáli sem er yfir á fallega, náttúrulega íslensku. "
            "Nota þegar LLM svar þarf fágun eða þýðingu yfir á íslensku."
        )

    async def run(self, text: str = "") -> str:
        """
        kwargs:
          text: inntakstexti
        Skilar: þýddur texti á íslensku
        """
        return await _translate_skill.run(text=text)
