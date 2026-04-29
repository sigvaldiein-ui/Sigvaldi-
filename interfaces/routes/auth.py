"""OIDC Auðkenni routes — Sprint 73 Fasi 3."""
import logging
import os
import secrets
import time
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

from interfaces.middleware.auth import (
    create_session_token,
    COOKIE_NAME,
    ACCESS_TOKEN_TTL,
)
from interfaces.models.user import hash_kennitala
from core.db_manager import finna_eda_bua_til_oidc_user, uppfaera_oidc_user

logger = logging.getLogger("alvitur.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Auðkenni OIDC config ---
AUDKENNI_CLIENT_ID = os.getenv("AUDKENNI_CLIENT_ID")
AUDKENNI_CLIENT_SECRET = os.getenv("AUDKENNI_CLIENT_SECRET")
AUDKENNI_BASE_URL = os.getenv("AUDKENNI_BASE_URL", "https://textq.audkenni.is:443/sso/")

if not AUDKENNI_CLIENT_ID or not AUDKENNI_CLIENT_SECRET:
    raise RuntimeError("AUDKENNI_CLIENT_ID and AUDKENNI_CLIENT_SECRET must be set")

REDIRECT_URI = os.getenv(
    "AUDKENNI_REDIRECT_URI",
    "https://alvitur.is/api/auth/callback",
)

# --- OAuth client ---
oauth = OAuth()
oauth.register(
    name="audkenni",
    client_id=AUDKENNI_CLIENT_ID,
    client_secret=AUDKENNI_CLIENT_SECRET,
    server_metadata_url=f"{AUDKENNI_BASE_URL}/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile kennitala",
        "code_challenge_method": "S256",
    },
)

# --- State cache (CSRF vörn) ---
_state_cache: dict[str, float] = {}
STATE_TTL = 600  # 10 mínútur


def _clean_state_cache():
    """Hreinsar útrunnin state."""
    now = time.time()
    expired = [s for s, exp in _state_cache.items() if exp < now]
    for s in expired:
        del _state_cache[s]


@router.get("/login")
async def login(request: Request):
    """Framsenda notanda á Auðkenni innskráningu."""
    _clean_state_cache()

    state = secrets.token_urlsafe(32)
    _state_cache[state] = time.time() + STATE_TTL

    redirect_uri = REDIRECT_URI
    return await oauth.audkenni.authorize_redirect(
        request,
        redirect_uri,
        state=state,
        code_challenge_method="S256",
    )


@router.get("/callback")
async def callback(request: Request):
    """Auðkenni sendir hingað eftir innskráningu."""
    _clean_state_cache()

    state = request.query_params.get("state")
    if not state or state not in _state_cache:
        logger.warning(f"OIDC callback: invalid or expired state={state}")
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    del _state_cache[state]

    try:
        token = await oauth.audkenni.authorize_access_token(request)
    except OAuthError as e:
        logger.error(f"OIDC token error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.audkenni.userinfo(token=token)

    kennitala = userinfo.get("kennitala") or userinfo.get("sub")
    nafn = userinfo.get("name", "")
    email = userinfo.get("email", "")

    if not kennitala:
        logger.error("OIDC callback: engin kennitala í userinfo")
        raise HTTPException(status_code=400, detail="Kennitala vantar í Auðkenni svari")

    kennitala_hash = hash_kennitala(kennitala)
    user = finna_eda_bua_til_oidc_user(kennitala)
    user_id = user["id"]
    if nafn or email:
        uppfaera_oidc_user(user_id, nafn=nafn, email=email)

    session_token = create_session_token(user_id, kennitala_hash)

    frontend_redirect = os.getenv("AUDKENNI_POST_LOGIN_URL", "/hvelfing")

    response = RedirectResponse(url=frontend_redirect, status_code=302)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        max_age=int(ACCESS_TOKEN_TTL.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    logger.info(f"Notandi skráður inn: {nafn}, kennitala_hash={kennitala_hash[:12]}...")
    return response


@router.get("/logout")
async def logout():
    """Eyðir session cookie."""
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@router.get("/session")
async def session(request: Request):
    """Skilar upplýsingum um núverandi session (ef einhver)."""
    user = getattr(request.state, "user", None)
    if user:
        return {"logged_in": True, "user_id": user["user_id"]}
    return {"logged_in": False}
