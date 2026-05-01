"""OIDC service — Auðkenni innskráning með PKCE."""
import logging
import secrets
import time
import hashlib
import base64
from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger("alvitur.oidc")

# OAuth client
oauth = OAuth()

# Configuration (úr env)
AUDKENNI_CLIENT_ID = None
AUDKENNI_CLIENT_SECRET = None
AUDKENNI_BASE_URL = None
REDIRECT_URI = "https://alvitur.is/auth/callback"

# Caches
_state_cache = {}
_nonce_cache = {}
_pkce_verifier_cache = {}

def _clean_state_cache(max_age_seconds=300):
    """Hreinsa göml state entries (default 5 mín)."""
    now = time.time()
    expired = [s for s, t in _state_cache.items() if now - t > max_age_seconds]
    for s in expired:
        _state_cache.pop(s, None)
        _nonce_cache.pop(s, None)
        _pkce_verifier_cache.pop(s, None)


def generate_pkce_pair():
    """Generates PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)[:128]
    code_challenge = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip("=")
    return code_verifier, code_challenge


def init_oidc():
    """Uppsetning á OIDC client — verður kallað eftir að env er lesið."""
    global AUDKENNI_CLIENT_ID, AUDKENNI_CLIENT_SECRET, AUDKENNI_BASE_URL
    import os
    
    AUDKENNI_CLIENT_ID = os.getenv("AUDKENNI_CLIENT_ID")
    AUDKENNI_CLIENT_SECRET = os.getenv("AUDKENNI_CLIENT_SECRET")
    AUDKENNI_BASE_URL = os.getenv("AUDKENNI_BASE_URL")
    
    if not all([AUDKENNI_CLIENT_ID, AUDKENNI_CLIENT_SECRET, AUDKENNI_BASE_URL]):
        logger.error("Missing Auðkenni configuration")
        return False
    
    # Register client (for token exchange, not authorization URL)
    oauth.register(
        name="audkenni",
        client_id=AUDKENNI_CLIENT_ID,
        client_secret=AUDKENNI_CLIENT_SECRET,
        server_metadata_url=f"{AUDKENNI_BASE_URL}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile"},
    )
    logger.info(f"OIDC client registered with issuer: {AUDKENNI_BASE_URL}")
    return True


async def build_login_url(request: Request) -> str:
    """Býr til Auðkenni login slóð með PKCE. Skilar URL sem notandi er sendur á."""
    # Try to initialize if client missing
    try:
        _ = oauth.audkenni
    except AttributeError:
        init_oidc()
    
    _clean_state_cache()
    
    state = secrets.token_hex(16)
    nonce = secrets.token_hex(8)
    code_verifier, code_challenge = generate_pkce_pair()
    
    _state_cache[state] = time.time()
    _nonce_cache[state] = nonce
    _pkce_verifier_cache[state] = code_verifier
    
    # Build URL manually with PKCE
    auth_url = (
        f"{AUDKENNI_BASE_URL}/authorize?"
        f"response_type=code"
        f"&client_id={AUDKENNI_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid+profile"
        f"&state={state}"
        f"&nonce={nonce}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    
    logger.info(f"Auðkenni login hafið — state={state[:8]}...")
    return auth_url


async def handle_callback(request: Request) -> JSONResponse:
    """Vinnur úr Auðkenni callback með PKCE verification."""
    from services.user_service import create_user_from_kennitala
    from interfaces.middleware.auth import create_session_token
    
    _clean_state_cache()
    
    # Verify state
    state = request.query_params.get("state")
    if not state or state not in _state_cache:
        logger.warning(f"Invalid state in callback: {state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Get code_verifier from cache
    code_verifier = _pkce_verifier_cache.get(state)
    if not code_verifier:
        logger.warning(f"No PKCE verifier for state: {state}")
        raise HTTPException(status_code=400, detail="Missing PKCE verifier")
    
    # Exchange code for token with PKCE
    code = request.query_params.get("code")
    if not code:
        logger.warning("No code in callback")
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    try:
        token = await oauth.audkenni.authorize_access_token(
            request,
            code_verifier=code_verifier,
        )
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=400, detail="Token exchange failed")
    
    # Get user info
    userinfo = token.get("userinfo")
    if not userinfo:
        logger.error("No userinfo in token response")
        raise HTTPException(status_code=400, detail="No user information")
    
    # Extract kennitala
    kennitala = userinfo.get("sub") or userinfo.get("kennitala")
    if not kennitala:
        logger.error(f"Missing kennitala in userinfo: {userinfo.keys()}")
        raise HTTPException(status_code=400, detail="Missing kennitala")
    
    # Create or get user
    user = await create_user_from_kennitala(kennitala)
    
    # Create session token
    session_token = create_session_token(user["id"], user["kennitala_hash"])
    
    # Create response with cookie
    response = JSONResponse({
        "logged_in": True,
        "user": {"id": user["id"], "name": user.get("name", "Notandi")}
    })
    response.set_cookie(
        key="alvitur_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900,
    )
    
    logger.info(f"User logged in: {kennitala[:4]}***")
    return response


async def build_logout_url(request: Request) -> str:
    """Býr til Auðkenni útskráningarslóð."""
    return "/"


async def get_user_info(request: Request) -> dict:
    """Sækir upplýsingar um innskráðan notanda úr session."""
    from interfaces.middleware.auth import decode_session_token
    
    token = request.cookies.get("alvitur_session")
    if not token:
        return {"logged_in": False}
    
    try:
        payload = decode_session_token(token)
        return {
            "logged_in": True,
            "user_id": int(payload["sub"]),
            "kennitala_hash": payload["kennitala_hash"],
        }
    except Exception:
        return {"logged_in": False}


async def get_session_info(request: Request) -> dict:
    """Skilar upplýsingum um núverandi session."""
    return await get_user_info(request)


async def refresh_session(request: Request) -> dict:
    """Endurnýjar session ef nálægt expiry."""
    return await get_user_info(request)


async def clear_session(request: Request):
    """Hreinsar session cookie."""
    pass


async def validate_session(request: Request) -> bool:
    """Staðfestir hvort session sé gilt."""
    info = await get_user_info(request)
    return info.get("logged_in", False)
