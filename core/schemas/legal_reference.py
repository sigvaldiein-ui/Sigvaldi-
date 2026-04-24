"""Sprint 68 B.1 — Canonical Icelandic legal reference schema (v0.3).

Empirical basis: snapshot 157a (2026-04-24), 3 lög, 1035 pinpoints.
See docs/SPRINT68_B1_SCHEMA.md for the tíðnitafla.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

Jurisdiction = Literal["IS", "EU"]
ReferenceType = Literal[
    "document",           # "Lög nr. 118/2016"
    "external_pinpoint",  # "19. gr. laga nr. 79/2008"
    "internal_pinpoint",  # "3. tl. 2. mgr. 36. gr." (same law)
    "sbr_reference",      # "sbr. 22. gr."
    "grein_range",        # "10.–16. gr."
    "eu_directive",       # "tilskipun ESB nr. 1215/2012"
]

ROMAN_TO_INT = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}


class LegalReference(BaseModel):
    """Canonical citation of an Icelandic law or pinpoint within one.

    Supports document-level refs, internal pinpoints (1035:1 dominant),
    external pinpoints, sbr-edges, grein ranges, and EU directives.
    """
    model_config = {"extra": "forbid", "frozen": False}

    # Jurisdiction
    source_jurisdiction: Jurisdiction = "IS"

    # Document identity (None => internal pinpoint within current law)
    law_nr: Optional[int] = Field(None, ge=1, le=9999)
    law_year: Optional[int] = Field(None, ge=1874, le=2100)
    law_title: Optional[str] = None

    # Pinpoint hierarchy (from coarse to fine)
    kafli_roman: Optional[str] = None
    kafli_int: Optional[int] = Field(None, ge=1, le=30)
    grein: Optional[int] = Field(None, ge=1, le=500)
    grein_range_end: Optional[int] = Field(None, ge=1, le=500)
    malsgrein: Optional[int] = Field(None, ge=1, le=20)
    tolulidur: Optional[int] = Field(None, ge=1, le=50)
    stafslidur: Optional[str] = Field(None, max_length=2)

    # Classification
    reference_type: ReferenceType

    # Audit trail
    raw_form: str = Field(..., min_length=2)
    source_url: Optional[str] = None
    source_publisher: str = "Alþingi"
    snapshot_version: Optional[str] = "157a"
    snapshot_date: str = "2026-04-24"

    @model_validator(mode="after")
    def _normalize_kafli(self) -> "LegalReference":
        if self.kafli_roman and self.kafli_int is None:
            self.kafli_int = ROMAN_TO_INT.get(self.kafli_roman.upper())
        return self

    @model_validator(mode="after")
    def _external_requires_law(self) -> "LegalReference":
        if self.reference_type == "external_pinpoint":
            if self.law_nr is None or self.law_year is None:
                raise ValueError(
                    "external_pinpoint requires law_nr and law_year"
                )
        return self

    @model_validator(mode="after")
    def _range_requires_end(self) -> "LegalReference":
        if self.reference_type == "grein_range":
            if self.grein is None or self.grein_range_end is None:
                raise ValueError(
                    "grein_range requires both grein and grein_range_end"
                )
            if self.grein_range_end <= self.grein:
                raise ValueError(
                    "grein_range_end must be greater than grein"
                )
        return self

    def to_canonical_string(self) -> str:
        """Render back to canonical Icelandic form for citation display."""
        parts = []
        if self.stafslidur:
            parts.append(f"{self.stafslidur}-liður")
        if self.tolulidur:
            parts.append(f"{self.tolulidur}. tölul.")
        if self.malsgrein:
            parts.append(f"{self.malsgrein}. mgr.")
        if self.grein and self.grein_range_end:
            parts.append(f"{self.grein}.–{self.grein_range_end}. gr.")
        elif self.grein:
            parts.append(f"{self.grein}. gr.")
        tail = " ".join(parts)
        if self.law_nr and self.law_year:
            lawref = f"laga nr. {self.law_nr}/{self.law_year}"
            if self.law_title:
                lawref += f" {self.law_title}"
            return f"{tail} {lawref}".strip()
        return tail or f"Lög nr. {self.law_nr}/{self.law_year}"
