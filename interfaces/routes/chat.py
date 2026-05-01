from fastapi import APIRouter, Request, Depends
from interfaces.middleware.auth import require_auth
import logging

logger = logging.getLogger("alvitur.chat")

router = APIRouter()

@router.post("/api/chat")
async def chat_endpoint(request: Request, user = Depends(require_auth)):
    """Sprint 45: Production chat endpoint.
    Sprint 46 Phase 1: Quota check + CF-Connecting-IP fix.
    """
    try:
        # CF-Connecting-IP has priority (real user IP behind Cloudflare)
        client_ip = request.headers.get("CF-Connecting-IP")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        # Quota check (placeholder)
        logger.info(f"Chat request from user {user.get('user_id') if user else 'anonymous'} IP {client_ip}")
        
        # Temporary response until AI integration
        return {"response": "Alvitur er í þróun. Vinsamlegast reyndu aftur síðar.", "success": True}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "Villa kom upp. Reyndu aftur.", "success": False}
