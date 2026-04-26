"""Pydantic request/response models for Alvitur.

Sprint 71 Track A.4c — extracted from interfaces/web_server.py.
"""
from typing import Optional
from pydantic import BaseModel, Field, validator

class ChatBeidni(BaseModel):
    """Inntak fyrir /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Skilaboð frá notanda",
    )
    user_id: str = Field(
        default="anonymous",
        max_length=64,
        description="Notandaauðkenni (tímabundið, skipt út á Fasa 3)",
    )

    @validator("message")
    def hreinsa_skilabus(cls, v: str) -> str:
        """Þrífa og sannreyna skilaboð."""
        hrein = v.strip()
        if not hrein:
            raise ValueError("Skilaboð má ekki vera tómt")
        return hrein


class ChatSvar(BaseModel):
    """Úttak frá /api/chat."""
    response: str
    timestamp: str
    # [FASI-2] Bæta við: model_used, tokens_used, search_used
    # [FASI-3] Bæta við: query_remaining


class HeilsusvarModel(BaseModel):
    """Úttak frá /api/health."""
    status: str
    version: str
    timestamp: str
    fasi: str
