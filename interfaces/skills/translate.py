# interfaces/skills/translate.py
"""
Sprint 56 — TranslateSkill.
Færir _polish() úr chat_routes.py yfir í Skill.
DeepSeek V3-0324 þýðir/fágar LLM svar yfir á fallega íslensku.
"""
import os
import httpx
import logging
from interfaces.skills.base import BaseSkill
from interfaces.config import POLISH_MODEL

logger = logging.getLogger("alvitur.web")

_POLISH_SYSTEM = (
    "You receive text in any language. "
    "Translate it to fluent, natural Icelandic. "
    "Rules: no markdown symbols (*, #, **), no bullet points unless the original uses them, "
    "natural sentence flow, no neologisms — if a word does not exist in Icelandic, "
    "describe it in a short phrase instead. "
    "Reply with the translated text only. Nothing else."
)


class TranslateSkill(BaseSkill):
    """Þýðir/fágar texta yfir á fallega íslensku með DeepSeek V3-0324."""

    @property
    def name(self) -> str:
        return "translate"

    async def run(self, text: str = "", key: str = "") -> str:
        """
        Þýðir texta yfir á íslensku.
        kwargs:
          text: inntakstexti
          key: OpenRouter API lykill
        Skilar: þýddur texti — fallback upprunalegi texti ef villa
        """
        if not text:
            return text

        api_key = key or os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return text

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://alvitur.is",
                    },
                    json={
                        "model": POLISH_MODEL,
                        "messages": [
                            {"role": "system", "content": _POLISH_SYSTEM},
                            {"role": "user", "content": text},
                        ],
                        "max_tokens": 1200,
                        "temperature": 0.3,
                    },
                    timeout=20.0,
                )
                r.raise_for_status()
                result = r.json()["choices"][0]["message"]["content"].strip()
                logger.info(
                    "[ALVITUR] translate ok model=%s chars_in=%d chars_out=%d",
                    POLISH_MODEL, len(text), len(result),
                )
                return result
        except Exception as e:
            logger.warning("[ALVITUR] translate villa (graceful degradation): %s", e)
            return text
