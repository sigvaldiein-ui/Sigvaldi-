# interfaces/skills/extract.py
"""
Sprint 56 — ExtractSkill.
Dregur út citations og entities úr texta.
Skilar lista af dicts með title, source, date.
"""
import os
import httpx
import logging
import json
from interfaces.skills.base import BaseSkill
from interfaces.config import get_model

logger = logging.getLogger("alvitur.web")


class ExtractSkill(BaseSkill):
    """Dregur út citations og entities úr texta."""

    @property
    def name(self) -> str:
        return "extract"

    async def run(
        self,
        text: str = "",
        key: str = "",
        tier: str = "general",
    ) -> list[dict]:
        """
        Extraktar citations úr texta.
        kwargs:
          text: inntakstexti
          key: OpenRouter API lykill
          tier: 'general' eða 'vault'
        Skilar: listi af dicts [{title, source, date}] — fallback [] ef villa
        """
        if not text:
            return []

        api_key = key or os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return []

        model = get_model(tier)
        prompt = (
            "Extract all citations, legal references, and sources from the following text. "
            "Return a JSON array of objects with keys: title, source, date. "
            "If no citations found, return []. "
            "Return only the JSON array, nothing else.\n\n"
            f"Text: {text[:2000]}"
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
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 600,
                        "temperature": 0,
                    },
                    timeout=15.0,
                )
                r.raise_for_status()
                raw = r.json()["choices"][0]["message"]["content"].strip()
                citations = json.loads(raw)
                if not isinstance(citations, list):
                    return []
                logger.info(
                    "[ALVITUR] extract ok model=%s citations=%d",
                    model, len(citations),
                )
                return citations
        except Exception as e:
            logger.warning("[ALVITUR] extract villa (graceful degradation): %s", e)
            return []
