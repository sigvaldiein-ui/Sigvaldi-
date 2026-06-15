from pathlib import Path

def _load_jwt_key(key_type="private"):
    """Les JWT lykil úr PEM skrá ef slóð er til, annars úr env."""
    env_key = f"JWT_{key_type.upper()}_KEY"
    path_key = f"JWT_{key_type.upper()}_KEY_PATH"
    path = os.environ.get(path_key, "")
    if path and Path(path).exists():
        with open(path, 'r') as f:
            return f.read()
    return os.environ.get(env_key, "dummy-dev-key")
"""Magic Link routes — POST request, GET verify."""
import logging, time, os, secrets, aiosqlite, jwt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.magic_email import send_magic_link

logger = logging.getLogger("alvitur.magic")
router = APIRouter(prefix="/api/auth/magic", tags=["magic"])
DB = "/workspace/Sigvaldi-/state_store.db"

RATE_LIMIT = {}  # email -> list of timestamps

def _rate_check(email: str) -> bool:
    now = time.time()
    times = RATE_LIMIT.get(email, [])
    times = [t for t in times if now - t < 900]
    RATE_LIMIT[email] = times
    if len(times) >= 3:
        return False
    times.append(now)
    return True

@router.post("/request")
async def magic_request(request: Request):
    try:
        body = await request.json()
        email = body.get("email", "").strip().lower()
    except Exception:
        return JSONResponse({"ok": True})
    if not email or "@" not in email:
        return JSONResponse({"ok": True})
    if not _rate_check(email):
        return JSONResponse({"ok": True})
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT sub FROM users WHERE email = ? AND active = 1", (email,))
        row = await cur.fetchone()
        if not row:
            return JSONResponse({"ok": True})
        user_sub = row[0]
        token = secrets.token_urlsafe(32)
        expires = time.time() + 600
        await db.execute("INSERT INTO magic_tokens (token, user_sub, expires_at, used) VALUES (?, ?, ?, 0)", (token, user_sub, expires))
        await db.commit()
    send_magic_link(email, token)
    return JSONResponse({"ok": True})

@router.get("/verify")
async def magic_verify(token: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_sub, expires_at, used FROM magic_tokens WHERE token = ?", (token,))
        row = await cur.fetchone()
        if not row:
            return JSONResponse({"error": "Ógildur tengill"}, status_code=401)
        user_sub, expires_at, used = row
        if used:
            return JSONResponse({"error": "Tengill þegar notaður"}, status_code=401)
        if time.time() > expires_at:
            return JSONResponse({"error": "Tengill útrunninn"}, status_code=401)
        await db.execute("UPDATE magic_tokens SET used = 1 WHERE token = ?", (token,))
        cur2 = await db.execute("SELECT org_id, tier FROM users WHERE sub = ? AND active = 1", (user_sub,))
        urow = await cur2.fetchone()
        if not urow:
            return JSONResponse({"error": "Notandi ekki virkur"}, status_code=401)
        org_id, tier = urow
        await db.commit()
    key = _load_jwt_key("private")
    payload = {"sub": user_sub, "org_id": org_id, "tier": tier, "jti": secrets.token_hex(16), "iat": int(time.time()), "exp": int(time.time()) + 3600}
    access_token = jwt.encode(payload, key, algorithm="RS256")
    return {"access_token": access_token, "token_type": "bearer"}
