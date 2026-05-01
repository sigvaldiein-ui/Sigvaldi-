# interfaces/skills/summarize.py
"""
Sprint 56 — SummarizeSkill.
Tekur texta og skilar stuttri samantekt á íslensku.
"""
import os
import httpx
import logging
from interfaces.skills.base import BaseSkill
from interfaces.config import get_model

logger = logging.getLogger("alvitur.web")


class SummarizeSkill(BaseSkill):
    """Texta samantekt — skilar 3-5 setningum á íslensku."""

    @property
    def name(self) -> str:
        return "summarize"

    async def run(
        self,
        text: str = "",
        key: str = "",
        tier: str = "general",
        max_tokens: int = 400,
    ) -> str:
        """
        Samantekt á texta.
        kwargs:
          text: inntakstexti
          key: OpenRouter API lykill
          tier: 'general' eða 'vault'
          max_tokens: hámark tóknar í svari
        Skilar: samantekt — fallback tómur strengur ef villa
        """
        if not text:
            return ""

        api_key = key or os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return ""

        model = get_model(tier)
        prompt = f"Dragðu saman eftirfarandi texta í 3-5 setningum á íslensku:\n\n{text[:3000]}"

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://alvitur.is",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": 0.3,
                    },
                    timeout=20.0,
                )
                r.raise_for_status()
                result = r.json()["choices"][0]["message"]["content"].strip()
                logger.info(
                    "[ALVITUR] summarize ok model=%s chars_in=%d chars_out=%d",
                    model, len(text), len(result),
                )
                return result
        except Exception as e:
            logger.warning("[ALVITUR] summarize villa (graceful degradation): %s", e)
            return ""
