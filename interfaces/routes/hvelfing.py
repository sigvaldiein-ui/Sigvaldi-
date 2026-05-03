"""Hvelfingin — sérstök greiningarleið Alvitur.is (Sprint 76b).

Endpoints:
- GET /api/v1/hvelfing/health  — Hvelfingar lifecheck
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("alvitur.hvelfing")

router = APIRouter()


@router.get("/api/v1/hvelfing/health")
async def hvelfing_health():
    """Hvelfingarheilsa — létt lifecheck."""
    return JSONResponse(content={
        "hvelfing": "lifandi",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fasi": "beta",
    })
