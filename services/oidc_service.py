"""OIDC Auðkenni service — einangrar OAuth rökfræði frá routes (Sprint 74 Fasi 3)."""
import logging
import os
import secrets
import time

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse, RedirectResponse

from interfaces.middleware.auth import (
    create_session_token,
    COOKIE_NAME,
    ACCESS_TOKEN_TTL,
)
from services.user_service import finna_eda_bua_til_oidc_user, uppfaera_oidc_user

logger = logging.getLogger("alvitur.services.oidc")

# --- Auðkenni OIDC config ---
AUDKENNI_CLIENT_ID = os.getenv("AUDKENNI_CLIENT_ID")
AUDKENNI_CLIENT_SECRET = os.getenv("AUDKENNI_CLIENT_SECRET")
AUDKENNI_BASE_URL = os.getenv("AUDKENNI_BASE_URL", "https://textq.audkenni.is:443/sso")

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
    code_challenge_method='S256',
    client_kwargs={
        "scope": "openid profile",
        "token_endpoint_auth_method": "client_secret_basic",
    },
)

# --- State cache (CSRF vörn) ---
_state_cache: dict[str, float] = {}


def _clean_state_cache():
    """Hreinsar útrunnin state úr skyndiminni."""
    now = time.time()
    expired = [k for k, v in _state_cache.items() if now - v > 600]
    for k in expired:
        del _state_cache[k]


async def build_login_url(request: Request) -> str:
    """Býr til Auðkenni login slóð. Skilar URL sem notandi er sendur á."""
    _clean_state_cache()

    state = secrets.token_hex(16)
    nonce = secrets.token_hex(8)
    _state_cache[state] = time.time()

    request.session["oidc_state"] = state
    request.session["oidc_nonce"] = nonce

    redirect_uri = REDIRECT_URI
    authorization_url = await oauth.audkenni.create_authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
    )

    logger.info(f"Auðkenni login hafið — state={state[:8]}...")
    return authorization_url


async def handle_callback(request: Request) -> JSONResponse:
    """Vinnur úr Auðkenni callback. Skilar JSON með session cookie."""
    state_from_cache = request.session.get("oidc_state")
    state_from_query = request.query_params.get("state")

    if not state_from_cache or state_from_cache != state_from_query:
        logger.warning("CSRF state mismatch — callback hafnað")
        raise HTTPException(status_code=403, detail="Ógilt authentication state")

    if state_from_query in _state_cache:
        del _state_cache[state_from_query]

    try:
        token = await oauth.audkenni.authorize_access_token(request)
    except OAuthError as e:
        logger.error(f"OAuth villa: {e}")
        raise HTTPException(status_code=401, detail="Auðkenning mistókst")

    userinfo = token.get("userinfo", {})
    kennitala = userinfo.get("sub", "")
    nafn = userinfo.get("name", "")
    email = userinfo.get("email", "")

    if not kennitala:
        logger.error("Engin kennitala í OIDC token")
        raise HTTPException(status_code=401, detail="Engin kennitala")

    user = finna_eda_bua_til_oidc_user(kennitala)

    if nafn or email:
        uppfaera_oidc_user(user["id"], nafn=nafn, email=email)

    session_token = create_session_token(user["id"], user["role"])

    logger.info(
        f"Innskráning tókst: user_id={user['id']}, "
        f"role={user['role']}, is_new={user['is_new']}"
    )

    response = JSONResponse({
        "logged_in": True,
        "user_id": user["id"],
        "role": user["role"],
        "is_new": user["is_new"],
    })

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        max_age=ACCESS_TOKEN_TTL,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


def build_logout_url() -> RedirectResponse:
    """Býr til útskráningar redirect (hreinsar cookie)."""
    response = RedirectResponse(url="/")
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    logger.info("Útskráning — cookie hreinsuð")
    return response


async def get_session_info(request: Request) -> JSONResponse:
    """Skilar session upplýsingum úr cookie."""
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return JSONResponse({"logged_in": False})

    from interfaces.middleware.auth import decode_session_token

    try:
        payload = decode_session_token(token)
        return JSONResponse({
            "logged_in": True,
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
        })
    except Exception:
        response = JSONResponse({"logged_in": False})
        response.delete_cookie(COOKIE_NAME)
        return response
