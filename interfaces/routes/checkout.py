"""Mock checkout / billing placeholder endpoints for Alvitur.

Sprint 71 Track A.4b — extracted from interfaces/web_server.py.

Endpoints:
- GET /mock-checkout          — placeholder for Stripe/Auðkenni.is checkout flow

Sprint 73 backlog: real billing integration.
"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from interfaces.static_content.html_pages import SHARED_HEAD, SHARED_STYLES

logger = logging.getLogger("alvitur.web")
router = APIRouter()


# TODO Sprint 72/73: build_success_page uses {placeholders} but never calls .format()
# Current behavior: HTML renders with literal {SHARED_HEAD}, {plan_display}, etc.
# Likely never reached in production (mock_success endpoint not in active flow).
# Fix: either add .format(SHARED_HEAD=SHARED_HEAD, plan_display=...) call,
#      convert string to f"""...""" with proper variable references,
#      or remove this code if endpoint is unused (verify with web_server.log grep).


# --- build_success_page ---
def build_success_page(plan: str, user_id: str) -> str:
    plan_names = {
        "brons": "Brons",
        "silfur": "Silfur",
        "gull": "Gull",
        "platina": "Platína",
    }
    plan_display = plan_names.get(plan.lower(), plan.capitalize())

    return """<!DOCTYPE html>
<html lang="is">
<head>
  <title>Greiðsla móttekin — Alvitur</title>
  {SHARED_HEAD}
  {SHARED_STYLES}
</head>
<body>
  <div class="subpage-center">
    <div class="subpage-card">
      <div class="success-check">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
      </div>
      <h1>Greiðsla móttekin!</h1>
      <p>Þetta er prófunarstaðfesting. Í raun myndi kerfið virkja <strong>{plan_display}</strong> áskrift fyrir notanda <code style="font-family: var(--font-mono); font-size: 0.8125rem; background: var(--bg-elevated); padding: 0.125rem 0.375rem; border-radius: var(--radius-sm);">{user_id}</code>.</p>

      <div class="checkout-summary" style="text-align: left;">
        <div class="checkout-row">
          <span class="label">Staða</span>
          <span class="value" style="color: var(--green);">✓ Staðfest (mock)</span>
        </div>
        <div class="checkout-row">
          <span class="label">Áskrift</span>
          <span class="value">{plan_display}</span>
        </div>
        <div class="checkout-row">
          <span class="label">Notandi</span>
          <span class="value" style="font-family: var(--font-mono); font-size: 0.8125rem;">{user_id}</span>
        </div>
      </div>

      <!-- Sprint 18: /minarsidur skipt út fyrir Telegram -->
      <a href="#" onclick="var el=document.getElementById(\'v5-txt\');if(el)el.scrollIntoView({{behavior:\'smooth\'}});return false;"  target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-lg" style="width: 100%; justify-content: center; margin-bottom: 0.75rem;">
        
      </a>
      <a href="/" class="btn btn-secondary" style="width: 100%; justify-content: center;">← Til baka á forsíðu</a>
    </div>
  </div>
</body>
</html>"""


# ─── Routes ───────────────────────────────────────────────────────────────────


# --- mock_success ---
@router.post("/api/webhook/mock_success", response_class=HTMLResponse)
async def mock_success(request: Request):
    # Samþykkja bæði form gögn og JSON
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    plan = data.get("plan", "unknown")
    user_id = data.get("user_id", "unknown")
    return HTMLResponse(content=build_success_page(plan, user_id))


# -- Sprint 66 pre-A: module-level PID lock file pointer (so refactor-safe) --
_pid_lock_fp = None
# -- /PID lock global --


if __name__ == "__main__":
    # -- Sprint 66 pre-A hotfix: single-instance PID lock --
    import fcntl as _fcntl_pl
    import sys as _sys_pl
    import os as _os_pl
    _PID_LOCK_PATH = _os_pl.getenv("ALVITUR_PID_LOCK", "/tmp/alvitur_web_server.lock")
    _pid_lock_fp = open(_PID_LOCK_PATH, "w", encoding="utf-8")
    try:
        _fcntl_pl.flock(_pid_lock_fp, _fcntl_pl.LOCK_EX | _fcntl_pl.LOCK_NB)
        _pid_lock_fp.write(str(_os_pl.getpid()))
        _pid_lock_fp.flush()
    except BlockingIOError:
        print(
            "[FATAL] web_server.py already running (lock: "
            + _PID_LOCK_PATH + ")",
            file=_sys_pl.stderr,
        )
        _sys_pl.exit(1)
    # -- /PID lock --
    uvicorn.run("web_server:app", host="0.0.0.0", port=int(__import__("os").environ.get("ALVITUR_PORT", "8000")))

