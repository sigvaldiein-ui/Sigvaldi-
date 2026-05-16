"""Session token middleware fyrir OIDC Auðkenni."""
import os, time, hashlib, hmac, json, logging
from fastapi import Request

logger = logging.getLogger("alvitur.auth.middleware")

COOKIE_NAME = "alvitur_session"
ACCESS_TOKEN_TTL = int(os.getenv("AUDKENNI_TOKEN_TTL", "3600"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")

def _sign(data: str) -> str:
    mac = hmac.new(SESSION_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}.{mac}"

def _unsign(signed: str) -> str | None:
    try:
        data, mac = signed.rsplit(".", 1)
        expected = hmac.new(SESSION_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(mac, expected):
            return data
    except Exception:
        pass
    return None

def create_session_token(user_id: int, role: str) -> str:
    payload = json.dumps({
        "user_id": user_id,
        "role": role,
        "iat": int(time.time()),
    })
    return _sign(payload)

def decode_session_token(token: str) -> dict | None:
    data = _unsign(token)
    if data:
        return json.loads(data)
    return None

def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_session_token(token)
    if payload and payload.get("iat", 0) + ACCESS_TOKEN_TTL < time.time():
        return None
    return payload
