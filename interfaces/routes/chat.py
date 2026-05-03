from fastapi import APIRouter, Request, Depends, HTTPException
from interfaces.middleware.auth import require_auth
from fastapi.responses import JSONResponse
import os, hashlib, logging

from interfaces.chat_routes import handle_chat
from interfaces.utils.quota import FREE_QUOTA, _quota_tracker_chat, _er_beta_fras, _er_beta_ip, _promota_beta
from interfaces.utils.openrouter import _log_intent

logger = logging.getLogger("alvitur.web")

router = APIRouter()

@router.post("/api/chat")
async def chat_endpoint(request: Request, user = None):
    """Sprint 45: Production chat endpoint.
    Sprint 46 Phase 1: Quota check + CF-Connecting-IP fix.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
    query = body.get("query", "").strip()
    # Hotfix: tier kemur annaðhvort úr JSON body eða X-Alvitur-Tier header.
    # Body hefur forgang — header er fallback fyrir eldri clients.
    _tier_body = body.get("tier", "").lower().strip()
    _tier_header = request.headers.get("X-Alvitur-Tier", "general").lower().strip()
    tier = _tier_body if _tier_body in ("general", "vault") else _tier_header
    if not query:
        return JSONResponse(status_code=422, content={"error_code": "empty_prompt"})

    # Sprint 46 Phase 1: IP quota check for /api/chat (was missing)
    import hashlib as _hl
    _master_key = os.environ.get("ALVITUR_MASTER_KEY_HASH", "")
    _req_key = request.headers.get("X-Master-Key", "")
    _is_admin = bool(_master_key and _req_key and _hl.sha256(_req_key.encode()).hexdigest() == _master_key)
    # CF-Connecting-IP has priority (real user IP behind Cloudflare)
    _client_ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    # ── Sprint 62: Beta check ──
    # Ef notandi skrifar beta-frasa → promotaður í 7 daga
    if _er_beta_fras(query):
        _promota_beta(_client_ip)
        logger.info(f"[BETA] {_client_ip} promotaður í beta-tier (7d)")
    _is_beta = _er_beta_ip(_client_ip)
    # ── /Sprint 62 Beta check ──
    _log_intent("chat", query, None, None, tier)

    _quota_count = _quota_tracker_chat.get(_client_ip, 0) + 1
    if not _is_admin and not _is_beta:
        _quota_tracker_chat[_client_ip] = _quota_count
    # Sprint 64 A1: samræma gate við tracker-update (bæta not _is_beta)
    if _quota_count > FREE_QUOTA and not _is_admin and not _is_beta:
        return JSONResponse(status_code=403, content={
            "success": False,
            "error": "Ókeypis prufutími er liðinn.",
            "error_code": "quota_exceeded",
            "upgrade_required": True,
            "upgrade_url": "/askrift",
            "message": "Þú hefur nýtt þr þr 5 ókeypis beiðnir. Uppfærðu til að halda áfram.",
        })

    return await handle_chat(request, query, tier)
