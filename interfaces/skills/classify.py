# interfaces/skills/classify.py
"""
Sprint 56 — ClassifySkill.
Færir classify() úr specialist_prompts.py yfir í Skill.
"""
import os
import httpx
import logging
from interfaces.skills.base import BaseSkill
from interfaces.config import CLASSIFY_MODEL

logger = logging.getLogger("alvitur.web")

DOMAINS = ["legal", "finance", "writing", "research", "general"]


class ClassifySkill(BaseSkill):
    """Domain flokkun — skilar einu af: legal, finance, writing, research, general."""

    @property
    def name(self) -> str:
        return "classify"

    async def run(self, text: str = "", key: str = "") -> str:
        """
        Flokkar fyrstu 500 stafi af text í domain.
        kwargs:
          text: inntakstexti
          key: OpenRouter API lykill
        Skilar: domain strengur — fallback 'general'
        """
        snippet = text.strip()[:500]
        if not snippet:
            return "general"

        api_key = key or os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return "general"

        prompt = (
            "Classify the following text into exactly one category. "
            "Reply with only one word — no explanation, no punctuation.\n"
            "Categories: legal, finance, writing, research, general\n\n"
            f"Text: {snippet}"
        )

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://alvitur.is",
                    },
                    json={
                        "model": CLASSIFY_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 5,
                        "temperature": 0,
                    },
                    timeout=10.0,
                )
                r.raise_for_status()
                raw = r.json()["choices"][0]["message"]["content"].strip().lower()
                domain = raw if raw in DOMAINS else "general"
                logger.info("[ALVITUR] classify domain=%s snippet=%r", domain, snippet[:60])
                return domain
        except Exception as e:
            logger.warning("[ALVITUR] classify villa (graceful degradation): %s", e)
            return "general"
