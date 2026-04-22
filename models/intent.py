"""
Sprint 64 Track A2 — Intent Data Model (Pydantic).

Staðsett í eigin skrá (EKKI web_server.py) til að forðast circular imports
þegar LangGraph Supervisor kemur í Sprint 65.

Ráðsamþykkt 22. apríl 2026:
- domain / reasoning_depth / adapter_hint / confidence_score / sensitivity / source_hint
- confidence_score er krafa frá degi 1 (ekki valfrjálst) til að leyfa
  LLM-fallback classification í Sprint 65 þegar score < 0.6.
- Frozen model: IntentResult er immutable þegar komið er í state-flow.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

Domain = Literal["legal", "financial", "general", "technical", "public"]
ReasoningDepth = Literal["fast", "standard", "deep"]
Sensitivity = Literal["low", "medium", "high"]
SourceHint = Literal["xlsx", "pdf", "docx", "text", "image", "audio", "unknown"]


class IntentResult(BaseModel):
    """
    Niðurstaða Intent Gateway klassifikeringar.
    Ber með sér öll ráðandi atriði fyrir niðurstreymi (LLM pick, adapter pick,
    sensitivity gating, logging).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: Domain = Field(
        ...,
        description="Efnissvið fyrirspurnarinnar. Ræður specialist-prompti.",
    )
    reasoning_depth: ReasoningDepth = Field(
        default="standard",
        description="Hversu djúpt LLM-in á að hugsa. 'fast' = Haiku/small; 'deep' = Opus/32B.",
    )
    adapter_hint: Optional[str] = Field(
        default=None,
        description="Valfrjáls ábending um adapter (t.d. 'tabular', 'rag', 'websearch').",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Líkindi á því að classification sé rétt. <0.6 → LLM fallback í S65.",
    )
    sensitivity: Sensitivity = Field(
        default="low",
        description="Gagnanæmni. 'high' → local-only (Leið B), enginn cloud call.",
    )
    source_hint: Optional[SourceHint] = Field(
        default=None,
        description="Skráarform eða input-gerð sem triggeraði classification.",
    )

    def should_fallback_to_llm(self, threshold: float = 0.6) -> bool:
        """Hjálparmethod fyrir Sprint 65 Supervisor."""
        return self.confidence_score < threshold

    def is_local_only(self) -> bool:
        """High-sensitivity → sovereign Leið B only (enginn OpenRouter call)."""
        return self.sensitivity == "high"
