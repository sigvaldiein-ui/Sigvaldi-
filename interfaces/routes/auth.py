"""OIDC Auðkenni routes — Sprint 73 Fasi 3 / Sprint 74 F3 (refactored)."""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from services.oidc_service import (
    build_login_url,
    handle_callback,
    build_logout_url,
    get_session_info,
)

logger = logging.getLogger("alvitur.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """Hefur innskráningarferli — sendir á Auðkenni."""
    authorization_url = await build_login_url(request)
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def callback(request: Request):
    """Auðkenni callback — vinnur úr OIDC svari."""
    return await handle_callback(request)


@router.get("/logout")
async def logout():
    """Útskráning — hreinsar session cookie."""
    return build_logout_url()


@router.get("/session")
async def session(request: Request):
    """Skilar núverandi session stöðu."""
    return await get_session_info(request)
