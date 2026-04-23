"""
Alvitur.is — Enterprise AI Landing Page
FastAPI server serving a one-page B2B SaaS funnel for Icelandic AI document analysis.

Sprint 16 breytingar:
  A) Web Chat Fasi 1 samþætt á /minarsidur (mock svör, engin V5 tenging)
  B) Sölutexti uppfærður — breiðari markhópur (lögfræðistofur, fjármálafyrirtæki, ráðgjafar)
  C) Dæmisögur ("Notendur segja") bætt við forsíðuna
  D) SecurityHeadersMiddleware bætt við (HSTS, CSP, X-Frame-Options, o.fl.)

Sprint 17 hotfix — Öryggi + UX:
  1) Netfang skipt: sigvaldi@fjarmalin.is / sigvaldiein@gmail.com → info@alvitur.is
  2) Beta upplýsingakassi bætt við forsíðuna undir hero (Telegram hlekkur)
  3) Session einangrun staðfest á /api/chat: engin shared state milli notenda

Sprint 18 — Hreinsa vefspjall / Web chat cleanup:
  1) Fjarlægður 'Mínar Síður' hlekkur úr nav
  2) Fjarlægður 'Opna á Telegram' hnappur úr nav (einungis Alvitur .is merki og valmynd eftir)
  3) Skipt út tveimur hnöppum undir beta kassa fyrir einn: ''
  4) /minarsidur route og build_minarsidur_page() commentuð út (geymd til sögunnar)
  5) Öll /minarsidur tenglar á forsíðu skipt út fyrir Telegram / mailto: hlekki
  6) Static mount (/static) commentuð út — var eingöngu notuð fyrir /minarsidur
  7) /api/chat route haldið (virkt — til framtíðarnotkunar á Fasa 2)

Sprint 19 — UI Hotfix (Aðal áætlun, innleiðsla Per):
  1) Telegram hraðhnappur aftur í navbar (sýnilegur á desktop + mobile)
  2) Hero padding þétt — meira efni above-the-fold
  3) Status pilla (hero-badge) smækkuð — minni visual weight
  4) Beta kassi fágaður — mildari litir, premium dökkt útlit
  5) Mobile-first fókus — Telegram hnappur alltaf sýnilegur, þéttara hero

Sprint 20 — V5.1 B2B Evidence Engine (Aðal áætlun, innleiðsla Per):
  1) H1 breytt í 'Alvitur – Við greinum gögnin sem skipta máli.'
  2) Undirfyrirsögn: Zero-Data, B2B markhópur
  3) Aðalhnappur: 'Óska eftir prufuaðgangi' → mailto:info@alvitur.is
  4) Drag-and-Drop PDF svæði bætt við (óvirkt viðmót, Evidence Engine tónn)
  5) Meta title og description uppfært
"""

import asyncio
import logging
import os

# Sprint 63 Track A: Load .env BEFORE any os.environ.get() calls
# Sprint 63 Track B1: env-aware loading — .env.dev if ALVITUR_ENV=dev
from dotenv import load_dotenv
import os as _os_init
_env_flag = _os_init.environ.get("ALVITUR_ENV", "prod")
_env_file = "/workspace/.env.dev" if _env_flag == "dev" else "/workspace/.env"
load_dotenv(_env_file)

# Sprint 63 Track A5: track server uptime for /api/diagnostics
import time as _time_init
_SERVER_START_TIME = _time_init.time()

# Sprint 63 Track A6: polish stub (restore removed-in-refactor function)
async def _polish_fn_txt(*args, **kwargs) -> str:
    """Async no-op polish stub — Sprint 63 Track A6.2.
    Caller notar 'await' svo þetta er async. Skilar textanum óbreyttum.
    TODO: bæta við raunverulegri íslenskri málfræðipúlisingu síðar.
    """
    text = args[0] if args else kwargs.get("text", "")
    return text if isinstance(text, str) else str(text)
import sys as _sys
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, validator
# Sprint 64 B2-V2: Intent Gateway observability (lazy import, never raises)
try:
    import sys as _sys, os as _os
    _here = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _here not in _sys.path:
        _sys.path.insert(0, _here)
    from core.intent_gateway import classify_intent as _classify_intent
    _INTENT_AVAILABLE = True
except Exception:
    _classify_intent = None
    _INTENT_AVAILABLE = False, validator
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# ─── Lög stillingar ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
import asyncio as _aio_ws
_VAULT_SEMAPHORE_WS = _aio_ws.Semaphore(1)
logger = logging.getLogger("alvitur.web")

# Sprint 54: pipeline_adapter skilar alltaf None — fallback path active

# ─── Gæðatak (Rate Limiting) ──────────────────────────────────────────────────
# Hámark 20 beiðnir á mínútu á hvert IP
GÆÐATAK_HÁMARK = int(os.environ.get("RATE_LIMIT", 20))
GÆÐATAK_GLUGGI = 60  # sekúndur

# Sprint 53b: Módel stillingar frá config.py — aldrei hardcoded
from interfaces.config import MODEL_LEIDA_A as _MODEL_LEIDA_A, MODEL_LEIDA_B as _MODEL_LEIDA_B

# Geymir: {ip_address: [tímastimplar]} fyrir síðustu 60 sekúndur
_gæðatak_minni: dict[str, list[float]] = defaultdict(list)


def athuga_gæðatak(ip: str) -> bool:
    """
    Sannprófar hvort IP tala sé yfir gæðataki.
    Skilar True ef beiðni er leyfð, False ef yfir mörk.
    Notar gluggatíma (sliding window) — einfaldasta útfærslan án Redis.
    """
    núna = time.time()
    _gæðatak_minni[ip] = [t for t in _gæðatak_minni[ip] if núna - t < GÆÐATAK_GLUGGI]
    if len(_gæðatak_minni[ip]) >= GÆÐATAK_HÁMARK:
        return False
    _gæðatak_minni[ip].append(núna)
    return True


def sækja_ip(request: Request) -> str:
    """Sækir raunverulegt IP-tölu notanda, tekur tillit til proxy."""
    for haus in ("cf-connecting-ip", "x-real-ip"):
        if ip := request.headers.get(haus):
            return ip.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


# ─── D) Öryggishausar Middleware ──────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Bætir við öryggishausum í hverja HTTP svörun.

    Hausar sem eru settir:
      - Strict-Transport-Security (HSTS)     : HTTPS alltaf, 1 ár
      - Content-Security-Policy              : XSS vörn
      - X-Frame-Options                      : Kemur í veg fyrir clickjacking
      - X-Content-Type-Options               : Kemur í veg fyrir MIME sniffing
      - Referrer-Policy                      : Takmarkar referrer upplýsingar
      - Permissions-Policy                   : Takmarkar vafra API aðgang
    """

    async def dispatch(self, request: Request, call_next):
        svar = await call_next(request)

        # HSTS — krefjast HTTPS í 1 ár með undirlénum
        svar.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # CSP — takmarkar hvaðan efni má sækja
        # Athugasemd: unsafe-inline er í stílar vegna innilagðra stíla (Fasi 1).
        # Í Fasa 2 færum við CSS í utanaðkomandi skrá og fjarlægjum unsafe-inline.
        svar.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://api.fontshare.com; "
            "font-src 'self' https://fonts.gstatic.com https://api.fontshare.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )

        # X-Frame-Options — kemur í veg fyrir að síðan sé sett í iframe (clickjacking)
        svar.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options — kemur í veg fyrir MIME tegundaspá
        svar.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer-Policy — takmarkar hvaðan referrer er sent
        svar.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy — takmarkar vafra API aðgang
        svar.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return svar


# ─── FastAPI forrit ────────────────────────────────────────────────────────────

app = FastAPI(
    title="Alvitur Enterprise AI",
    docs_url=None,   # Slökkva á Swagger UI í framleiðslu
    redoc_url=None,  # Slökkva á ReDoc í framleiðslu
)

# Sprint 43b: Custom 422 handler — add error_code for frontend compatibility
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Check if the error is specifically about a missing file field
    error_code = "validation_error"
    for err in exc.errors():
        if err.get("loc") and "file" in err.get("loc", []):
            error_code = "no_file"
            break
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "error_code": error_code,
            "detail": exc.errors(),
        },
    )

# Gzip þjöppun (sparar bandbreidd)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# D) Öryggishausar á allar beiðnir
app.add_middleware(SecurityHeadersMiddleware)

# Sprint 18: Static mount commentuð út — var eingöngu notuð fyrir /minarsidur vefspjall
from fastapi.staticfiles import StaticFiles
# import os as _os
_static_dir = "/workspace/mimir_net/interfaces/static"
# _os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ─── A) Gagnalíkön fyrir Web Chat API ────────────────────────────────────────

class ChatBeidni(BaseModel):
    """Inntak fyrir /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Skilaboð frá notanda",
    )
    user_id: str = Field(
        default="anonymous",
        max_length=64,
        description="Notandaauðkenni (tímabundið, skipt út á Fasa 3)",
    )

    @validator("message")
    def hreinsa_skilabus(cls, v: str) -> str:
        """Þrífa og sannreyna skilaboð."""
        hrein = v.strip()
        if not hrein:
            raise ValueError("Skilaboð má ekki vera tómt")
        return hrein


class ChatSvar(BaseModel):
    """Úttak frá /api/chat."""
    response: str
    timestamp: str
    # [FASI-2] Bæta við: model_used, tokens_used, search_used
    # [FASI-3] Bæta við: query_remaining


class HeilsusvarModel(BaseModel):
    """Úttak frá /api/health."""
    status: str
    version: str
    timestamp: str
    fasi: str


# ─── A) Mock svörþjónusta ─────────────────────────────────────────────────────
# [FASI-2]: Skipta þessum mock svörum út fyrir MimirCoreV5.process_message()

# Íslenskt velkomnarboð
VELKOMIN_BOÐ = (
    "Góðan daginn! Ég er **Alvitur**, íslenskur gervigreindaraðstoðarmaður "
    "sérhæfður í skjalagreiningu og lögfræðilegri rannsókn.\n\n"
    "Ég get aðstoðað þig með:\n"
    "- Greiningu á **ársreikningum** og fjárhagslegum skjölum\n"
    "- Leit og samantekt úr **íslenskum lögum og reglugerðum**\n"
    "- Samanburð á **samningum** og lagalegum gögnum\n"
    "- **Minnisblöð** og skýrslugerð á sekúndum\n\n"
    "Hvað get ég gert fyrir þig í dag?"
)

# ─── Shared Styles & Components ───────────────────────────────────────────────

SHARED_HEAD = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Alvitur – Traust og örugg íslensk gervigreind fyrir lögfræði, fjármál og stjórnsýslu. Við finnum frávik og samhengi á sekúndubrotum í lokuðu Zero-Data umhverfi.">
<meta property="og:title" content="Alvitur – Við greinum gögnin sem skipta máli.">
<meta property="og:description" content="Sérþjálfað gervigreindarkerfi fyrir íslenskar fagstofur. Greindu íslensk lög, samninga og ársreikninga á sekúndum.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://alvitur.is">
<meta property="og:locale" content="is_IS">
<meta property="og:site_name" content="Alvitur">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Alvitur — Íslensk gervigreind">
<meta name="twitter:description" content="Sérþjálfað gervigreindarkerfi fyrir endurskoðendur, lögfræðistofur og fjármálafyrirtæki.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@500,700,800&display=swap" rel="stylesheet">
"""

SHARED_STYLES = """
<style>
  /* ─── Reset & Base ─────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:              #080B12;
    --bg-elevated:     #0F1623;
    --bg-card:         #111827;
    --bg-card-hover:   #1a2436;
    --text-primary:    #F1F5F9;
    --text-secondary:  #94A3B8;
    --text-muted:      #64748B;
    --accent:          #6366F1;
    --accent-light:    #818CF8;
    --accent-glow:     rgba(99, 102, 241, 0.15);
    --accent-glow-strong: rgba(99, 102, 241, 0.25);
    --border:          rgba(148, 163, 184, 0.1);
    --border-strong:   rgba(148, 163, 184, 0.2);
    --green:           #34D399;
    --green-bg:        rgba(52, 211, 153, 0.1);
    --green-border:    rgba(52, 211, 153, 0.2);
    --font-display:    'Cabinet Grotesk', 'Inter', system-ui, sans-serif;
    --font-body:       'Inter', system-ui, sans-serif;
    --font-mono:       'JetBrains Mono', monospace;
    --radius-sm:       0.375rem;
    --radius-md:       0.5rem;
    --radius-lg:       0.75rem;
    --radius-xl:       1rem;
    --transition:      180ms cubic-bezier(0.16, 1, 0.3, 1);
  }

  html {
    scroll-behavior: smooth;
    scroll-padding-top: 5rem;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }

  body {
    min-height: 100dvh;
    font-family: var(--font-body);
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--bg);
  }

  ::selection {
    background: var(--accent-glow-strong);
    color: var(--text-primary);
  }

  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
    border-radius: var(--radius-sm);
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }

  img, picture, video, svg { display: block; max-width: 100%; height: auto; }
  a { color: inherit; text-decoration: none; }
  button { cursor: pointer; background: none; border: none; font: inherit; color: inherit; }
  h1, h2, h3, h4, h5, h6 { text-wrap: balance; line-height: 1.15; }
  p, li, figcaption { text-wrap: pretty; max-width: 72ch; }

  /* ─── Skip Link ────────────────────────────── */
  .skip-link {
    position: absolute;
    top: -100%;
    left: 1rem;
    z-index: 100;
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border-radius: var(--radius-md);
    font-weight: 600;
    font-size: 0.875rem;
  }
  .skip-link:focus {
    top: 1rem;
  }

  /* ─── Container ────────────────────────────── */
  .container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  /* ─── Nav ───────────────────────────────────── */
  .nav {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(8, 11, 18, 0.85);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border-bottom: 1px solid var(--border);
    transition: box-shadow var(--transition);
  }
  .nav.scrolled {
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  }
  .nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 4rem;
  }
  .nav-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }
  .nav-logo svg {
    width: 28px;
    height: 28px;
  }
  .nav-links {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }
  .nav-link {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    transition: color var(--transition);
  }
  .nav-link:hover { color: var(--text-primary); }

  /* Sprint 19 hotfix: Telegram hraðhnappur í navbar */
  .nav-telegram-btn {
    padding: 0.4rem 0.85rem;
    font-size: 0.8125rem;
    border-radius: var(--radius-md);
  }
  .nav-telegram-btn svg {
    flex-shrink: 0;
  }

  /* ─── Buttons ──────────────────────────────── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 600;
    border-radius: var(--radius-md);
    transition: all var(--transition);
    white-space: nowrap;
  }
  .btn-primary {
    background: var(--accent);
    color: white;
    box-shadow: 0 0 0 0 var(--accent-glow);
  }
  .btn-primary:hover {
    background: var(--accent-light);
    box-shadow: 0 0 24px var(--accent-glow-strong);
    transform: translateY(-1px);
  }
  .btn-secondary {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-strong);
  }
  .btn-secondary:hover {
    color: var(--text-primary);
    border-color: var(--text-muted);
    background: rgba(255,255,255,0.03);
  }
  .btn-lg {
    padding: 0.875rem 1.75rem;
    font-size: 1rem;
  }

  /* ─── Hero ─────────────────────────────────── */
  /* Sprint 19 hotfix: þéttara hero padding — meira above-the-fold */
  .hero {
    position: relative;
    padding: clamp(3.5rem, 8vw, 7rem) 0 clamp(2.5rem, 5vw, 5rem);
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -200px;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    height: 600px;
    background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }
  .hero-content {
    position: relative;
    z-index: 1;
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
  }
  /* Sprint 19 hotfix: smækkuð status pilla — ýtir minna innihaldi niður */
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    margin-bottom: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: var(--radius-xl);
    letter-spacing: 0.03em;
  }
  .hero-badge-dot {
    width: 6px;
    height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
  }
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
  }
  .hero h1 {
    font-family: var(--font-display);
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    margin-bottom: 1.5rem;
  }
  .hero h1 span {
    background: linear-gradient(135deg, var(--accent-light), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-sub {
    font-size: clamp(1rem, 1.5vw, 1.25rem);
    color: var(--text-secondary);
    max-width: 600px;
    margin: 0 auto 2.5rem;
    line-height: 1.7;
  }
  .hero-actions {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  /* ─── Sections ─────────────────────────────── */
  section {
    padding: clamp(4rem, 8vw, 7rem) 0;
  }
  .section-label {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--accent-light);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
  }
  .section-title {
    font-family: var(--font-display);
    font-size: clamp(1.75rem, 3.5vw, 2.5rem);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    margin-bottom: 1rem;
  }
  .section-desc {
    font-size: 1.0625rem;
    color: var(--text-secondary);
    max-width: 560px;
    line-height: 1.7;
  }
  .section-header {
    text-align: center;
    margin-bottom: clamp(3rem, 5vw, 4rem);
  }
  .section-header .section-desc {
    margin: 0 auto;
  }

  /* ─── Glass Cards ──────────────────────────── */
  .glass-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.6));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    transition: all var(--transition);
    backdrop-filter: blur(8px);
  }
  .glass-card:hover {
    border-color: var(--border-strong);
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.9), rgba(15, 22, 35, 0.7));
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }

  /* ─── Trust Section ────────────────────────── */
  .trust-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }
  .trust-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-glow);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: var(--radius-lg);
    margin-bottom: 1.25rem;
    color: var(--accent-light);
  }
  .trust-title {
    font-family: var(--font-display);
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .trust-desc {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }

  /* ─── Features Section ─────────────────────── */
  .features-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  .feature-card {
    position: relative;
    overflow: hidden;
  }
  .feature-card.featured {
    grid-column: span 2;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    align-items: center;
  }
  .feature-number {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--accent);
    margin-bottom: 0.75rem;
    font-weight: 500;
  }
  .feature-title {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .feature-desc {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
  }
  .feature-visual {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    min-height: 200px;
    background: rgba(99, 102, 241, 0.03);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(99, 102, 241, 0.08);
  }
  .code-block {
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    color: var(--text-secondary);
    line-height: 1.8;
    text-align: left;
    white-space: pre;
  }
  .code-block .kw { color: var(--accent-light); }
  .code-block .fn { color: var(--green); }
  .code-block .str { color: #F59E0B; }
  .code-block .cm { color: var(--text-muted); }

  /* ─── Problem/Solution ─────────────────────── */
  .problem-section {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.03), transparent);
  }
  .ps-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
    align-items: start;
  }
  .ps-card {
    padding: 2.5rem;
    border-radius: var(--radius-xl);
  }
  .ps-card.problem {
    background: rgba(239, 68, 68, 0.03);
    border: 1px solid rgba(239, 68, 68, 0.1);
  }
  .ps-card.solution {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.15);
  }
  .ps-card h3 {
    font-family: var(--font-display);
    font-size: 1.375rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }
  .ps-card.problem h3 { color: #F87171; }
  .ps-card.solution h3 { color: var(--accent-light); }
  .ps-card p {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 1.25rem;
  }
  .ps-list {
    list-style: none;
    padding: 0;
  }
  .ps-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    font-size: 0.9375rem;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
    line-height: 1.5;
  }
  .ps-list li svg {
    flex-shrink: 0;
    margin-top: 0.2rem;
  }

  /* ─── Pricing ──────────────────────────────── */
  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    align-items: start;
  }
  .pricing-card {
    position: relative;
    background: linear-gradient(180deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.5));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    transition: all var(--transition);
  }
  .pricing-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }
  .pricing-card.popular {
    border-color: var(--accent);
    box-shadow: 0 0 40px var(--accent-glow);
  }
  .pricing-card.popular::before {
    content: 'Vinsælast';
    position: absolute;
    top: -0.75rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.25rem 1rem;
    background: var(--accent);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: var(--radius-xl);
    white-space: nowrap;
  }
  .pricing-medal {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }
  .pricing-name {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }
  .pricing-target {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 1.25rem;
  }
  .pricing-price {
    margin-bottom: 1.5rem;
  }
  .pricing-amount {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }
  .pricing-period {
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  .pricing-features {
    list-style: none;
    padding: 0;
    margin-bottom: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }
  .pricing-features li {
    display: flex;
    align-items: flex-start;
    gap: 0.625rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }
  .pricing-features li svg {
    flex-shrink: 0;
    margin-top: 0.15rem;
    color: var(--accent-light);
  }
  .pricing-cta {
    width: 100%;
    text-align: center;
    justify-content: center;
  }

  /* ─── C) Dæmisögur (Testimonials) ─────────────────────── */
  .testimonials-section {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.02), transparent);
  }
  .testimonials-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }
  .testimonial-card {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.8), rgba(15, 22, 35, 0.6));
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    position: relative;
    transition: all var(--transition);
  }
  .testimonial-card:hover {
    border-color: var(--border-strong);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  }
  .testimonial-quote {
    font-size: 2rem;
    color: var(--accent);
    opacity: 0.4;
    line-height: 1;
    margin-bottom: 1rem;
    font-family: Georgia, serif;
  }
  .testimonial-text {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.75;
    margin-bottom: 1.5rem;
    font-style: italic;
  }
  .testimonial-author {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .testimonial-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--accent-glow);
    border: 1px solid rgba(99, 102, 241, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--accent-light);
    flex-shrink: 0;
    font-family: var(--font-display);
  }
  .testimonial-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.125rem;
  }
  .testimonial-role {
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  .testimonial-stars {
    display: flex;
    gap: 2px;
    margin-bottom: 1rem;
  }
  .testimonial-stars svg {
    width: 14px;
    height: 14px;
    color: #F59E0B;
    fill: #F59E0B;
  }

  /* ─── CTA Section ──────────────────────────── */
  .cta-section {
    text-align: center;
    position: relative;
  }
  .cta-section::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 400px;
    background: radial-gradient(ellipse, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
  }
  .cta-section .section-desc {
    margin: 0 auto 2rem;
  }

  /* ─── Footer ───────────────────────────────── */
  .footer {
    border-top: 1px solid var(--border);
    padding: 3rem 0 2rem;
    color: var(--text-muted);
    font-size: 0.8125rem;
  }
  .footer-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    text-align: center;
  }
  .footer-logo {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .footer-links {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }
  .footer-links a {
    color: var(--text-muted);
    transition: color var(--transition);
  }
  .footer-links a:hover { color: var(--text-secondary); }
  .footer-legal {
    color: var(--text-muted);
    line-height: 1.8;
  }
  .footer-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: var(--radius-xl);
  }

  /* ─── Beta Kassi ──────────────────────────── */
  .beta-kassi {
    margin: 0 auto 0;
    padding: clamp(1.25rem, 3vw, 2rem) 0;
  }
  /* Sprint 19 hotfix: fágaður Beta kassi — mildara, premium dökkt útlit */
  .beta-kassi-innði {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.04), rgba(20, 184, 166, 0.03));
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-xl);
    padding: clamp(1.25rem, 3vw, 1.75rem) clamp(1.25rem, 3vw, 2rem);
    position: relative;
    overflow: hidden;
  }
  .beta-kassi-innði::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(99,102,241,0.04) 0%, transparent 60%);
    pointer-events: none;
  }
  /* Sprint 19 hotfix: mildari beta-merki litir */
  .beta-kassi-merki {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    margin-bottom: 0.875rem;
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--text-muted);
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    text-transform: uppercase;
    letter-spacing: 0.07em;
  }
  .beta-kassi-merki-dot {
    width: 5px;
    height: 5px;
    background: var(--accent-light);
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
  }
  .beta-kassi-texti {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.75;
    margin-bottom: 1.25rem;
    max-width: 72ch;
  }
  .beta-kassi-hnappur {
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 700;
    color: white;
    background: linear-gradient(135deg, #6366F1, #14B8A6);
    border-radius: var(--radius-md);
    transition: all var(--transition);
    box-shadow: 0 0 0 0 rgba(99,102,241,0.3);
    white-space: nowrap;
  }
  .beta-kassi-hnappur:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(99,102,241,0.35);
    opacity: 0.93;
  }
  @media (max-width: 640px) {
    .beta-kassi-hnappur {
      width: 100%;
      justify-content: center;
    }
  }

  /* ─── Separator ────────────────────────────── */
  .divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-strong), transparent);
    margin: 0;
  }

  /* ─── Animations ───────────────────────────── */
  .fade-in {
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.6s ease-out, transform 0.6s ease-out;
  }
  .fade-in.visible {
    opacity: 1;
    transform: translateY(0);
  }

  /* ─── Mobile ───────────────────────────────── */
  @media (max-width: 768px) {
    .trust-grid { grid-template-columns: 1fr; }
    .features-grid { grid-template-columns: 1fr; }
    .feature-card.featured {
      grid-column: span 1;
      grid-template-columns: 1fr;
    }
    .ps-grid { grid-template-columns: 1fr; }
    .pricing-grid {
      grid-template-columns: 1fr;
      max-width: 400px;
      margin: 0 auto;
    }
    .testimonials-grid { grid-template-columns: 1fr; }
    .nav-link.desktop-only { display: none; }
    .hero h1 { font-size: clamp(2rem, 7vw, 2.5rem); }
    .container { padding: 0 1rem; }
    .hero-actions { flex-direction: column; align-items: center; }
  }

  @media (min-width: 769px) and (max-width: 1024px) {
    .pricing-grid { grid-template-columns: repeat(2, 1fr); }
    .features-grid { grid-template-columns: 1fr; }
    .feature-card.featured {
      grid-column: span 1;
      grid-template-columns: 1fr;
    }
    .testimonials-grid { grid-template-columns: repeat(2, 1fr); }
  }

  /* ─── Mobile nav menu ──────────────────────── */
  .mobile-menu-btn {
    display: none;
    width: 44px;
    height: 44px;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
  }
  /* Sprint 19 hotfix: mobile nav — Telegram hnappur sýnilegur, textatenglar í valmynd */
  @media (max-width: 768px) {
    .mobile-menu-btn { display: flex; }
    .nav-links {
      display: none;
      position: absolute;
      top: 4rem;
      left: 0;
      right: 0;
      flex-direction: column;
      background: rgba(8, 11, 18, 0.97);
      backdrop-filter: blur(16px);
      padding: 1.5rem;
      border-bottom: 1px solid var(--border);
      gap: 0.5rem;
    }
    .nav-links.open { display: flex; }
    .nav-links .nav-link,
    .nav-links .btn {
      width: 100%;
      text-align: center;
      padding: 0.75rem 1rem;
    }
    /* Telegram hraðhnappur alltaf sýnilegur á mobile */
    .nav-telegram-btn {
      padding: 0.35rem 0.7rem;
      font-size: 0.75rem;
      order: 2;
    }
    .mobile-menu-btn {
      order: 3;
    }
    /* Þéttara hero á mobile */
    .hero {
      padding: 2rem 0 1.5rem;
    }
    .hero-badge {
      font-size: 0.625rem;
      padding: 0.2rem 0.6rem;
      margin-bottom: 0.5rem;
    }
    .hero h1 {
      margin-bottom: 1rem;
    }
    .hero-sub {
      margin-bottom: 1.5rem;
    }
  }

  /* ─── Drag-and-Drop svæði — Sprint 20 V5.1 ─── */
  .dnd-section {
    padding: 2rem 0;
  }
  .dnd-zone {
    border: 2px dashed var(--border-strong);
    border-radius: var(--radius-xl);
    padding: clamp(2.5rem, 6vw, 4rem) clamp(1.5rem, 4vw, 3rem);
    text-align: center;
    background: rgba(99, 102, 241, 0.03);
    transition: border-color var(--transition), background var(--transition);
    cursor: default;
    user-select: none;
    position: relative;
  }
  .dnd-zone::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-xl);
    background: radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.06) 0%, transparent 70%);
    pointer-events: none;
  }
  .dnd-icon {
    color: var(--accent-light);
    opacity: 0.6;
    margin-bottom: 1.25rem;
  }
  .dnd-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  .dnd-sub {
    font-size: 0.9375rem;
    color: var(--text-muted);
    max-width: 480px;
    margin: 0 auto 1.25rem;
    line-height: 1.6;
  }
  .dnd-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  @media (max-width: 768px) {
    .dnd-zone { padding: 2rem 1rem; }
    .dnd-title { font-size: 1.0625rem; }
  }

  /* ─── Legal page styles — Sprint 21 ─────────── */
  .legal-date {
    font-size: 0.8125rem;
    color: var(--text-muted);
    margin-bottom: 1.5rem;
    font-style: italic;
  }
  .subpage-card h2 {
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 2rem 0 0.625rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
  }
  .subpage-card h2:first-of-type { border-top: none; margin-top: 1.5rem; }
  .subpage-card p { color: var(--text-secondary); line-height: 1.75; margin-bottom: 1rem; }
  .subpage-card a { color: var(--accent-light); text-decoration: underline; text-underline-offset: 2px; }

  /* ─── Subpage styles ───────────────────────── */
  .subpage-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100dvh;
    text-align: center;
    padding: 2rem;
  }
  .subpage-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 3rem;
    max-width: 500px;
    width: 100%;
  }
  .subpage-card h1 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }
  .subpage-card p {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    line-height: 1.7;
  }
  .input-field {
    width: 100%;
    padding: 0.75rem 1rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 0.9375rem;
    margin-bottom: 0.75rem;
    transition: border-color var(--transition);
  }
  .input-field:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  .input-field::placeholder { color: var(--text-muted); }
  .checkout-summary {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: left;
  }
  .checkout-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.9375rem;
    margin-bottom: 0.5rem;
  }
  .checkout-row .label { color: var(--text-secondary); }
  .checkout-row .value { color: var(--text-primary); font-weight: 600; }
  .checkout-total {
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
    margin-top: 0.75rem;
    font-size: 1.0625rem;
    font-weight: 700;
  }
  .success-check {
    width: 64px;
    height: 64px;
    margin: 0 auto 1.5rem;
    background: var(--green-bg);
    border: 2px solid var(--green-border);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--green);
  }

  /* ─── A) Web Chat stílar ─────────────────────── */
  /* Notuð á /minarsidur síðunni */
  .chat-page body {
    overflow: hidden;
  }
  .chat-haus {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    height: 3.75rem;
    background: rgba(8, 11, 18, 0.92);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 1.25rem;
    gap: 0.75rem;
  }
  .chat-til-baka {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 0.375rem 0.625rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition);
    white-space: nowrap;
  }
  .chat-til-baka:hover {
    color: var(--text-primary);
    background: rgba(255,255,255,0.05);
  }
  .chat-aðskilir {
    width: 1px;
    height: 1.25rem;
    background: var(--border-strong);
    flex-shrink: 0;
  }
  .chat-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 1.0625rem;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    flex: 1;
  }
  .chat-merki {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--green);
    background: var(--green-bg);
    border: 1px solid var(--green-border);
    border-radius: 999px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .chat-merki-dot {
    width: 6px;
    height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: þreifa 2s ease-in-out infinite;
  }
  @keyframes þreifa {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
  .chat-skipulag {
    display: flex;
    flex-direction: column;
    height: 100dvh;
    padding-top: 3.75rem;
  }
  .chat-saga {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem 0;
    scroll-behavior: smooth;
  }
  .chat-saga::-webkit-scrollbar { width: 6px; }
  .chat-saga::-webkit-scrollbar-track { background: transparent; }
  .chat-saga::-webkit-scrollbar-thumb {
    background: var(--border-strong);
    border-radius: 3px;
  }
  .chat-innri {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .boð-lína {
    display: flex;
    gap: 0.75rem;
    animation: renna-inn 0.25s ease-out;
  }
  @keyframes renna-inn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .boð-lína.ai-boð { justify-content: flex-start; }
  .boð-lína.ai-boð .boð-bubble {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
    padding: 0.875rem 1rem;
    max-width: 80%;
    color: var(--text-primary);
  }
  .boð-lína.notenda-boð { justify-content: flex-end; }
  .boð-lína.notenda-boð .boð-bubble {
    background: #3730A3;
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: var(--radius-lg) 0 var(--radius-lg) var(--radius-lg);
    padding: 0.875rem 1rem;
    max-width: 80%;
    color: white;
    word-break: break-word;
  }
  .boð-merki {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 2px;
  }
  .ai-merki {
    background: linear-gradient(135deg, var(--accent), #7c3aed);
    box-shadow: 0 0 12px var(--accent-glow);
  }
  .boð-tími {
    font-size: 0.6875rem;
    color: var(--text-muted);
    margin-top: 0.375rem;
    display: block;
  }
  .ai-boð .boð-tími { text-align: left; }
  .notenda-boð .boð-tími { text-align: right; }
  .boð-texti strong { font-weight: 600; }
  .boð-texti em { font-style: italic; color: var(--text-secondary); }
  .boð-texti code {
    font-family: var(--font-mono);
    font-size: 0.8125em;
    background: rgba(255,255,255,0.08);
    padding: 0.125em 0.375em;
    border-radius: 3px;
  }
  .boð-texti pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.875rem;
    overflow-x: auto;
    margin: 0.625rem 0;
  }
  .boð-texti pre code { background: none; padding: 0; font-size: 0.8125em; }
  .boð-texti ul, .boð-texti ol {
    padding-left: 1.375rem;
    margin: 0.375rem 0;
  }
  .boð-texti li { margin: 0.25rem 0; }
  .boð-texti a { color: var(--accent-light); text-decoration: underline; text-underline-offset: 2px; }
  .boð-texti p { margin: 0.375rem 0; }
  .boð-texti p:first-child { margin-top: 0; }
  .boð-texti p:last-child { margin-bottom: 0; }
  .boð-texti table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.75rem 0;
    font-size: 0.875em;
  }
  .boð-texti th, .boð-texti td {
    border: 1px solid var(--border-strong);
    padding: 0.5rem 0.75rem;
    text-align: left;
  }
  .boð-texti th {
    background: rgba(255,255,255,0.05);
    font-weight: 600;
    color: var(--text-secondary);
  }
  .boð-texti tr:nth-child(even) { background: rgba(255,255,255,0.02); }
  .hladning-rowr {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 0.375rem 0;
    min-height: 1.5rem;
  }
  .hladning-dot {
    width: 7px;
    height: 7px;
    background: var(--text-muted);
    border-radius: 50%;
    animation: bopp 1.2s ease-in-out infinite;
  }
  .hladning-dot:nth-child(2) { animation-delay: 0.2s; }
  .hladning-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bopp {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30%            { transform: translateY(-8px); opacity: 1; background: var(--accent-light); }
  }
  .inntak-sviði {
    flex-shrink: 0;
    background: rgba(8, 11, 18, 0.96);
    border-top: 1px solid var(--border);
    padding: 0.875rem 1.25rem 1rem;
  }
  .inntak-innri {
    max-width: 800px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .inntak-rowr {
    display: flex;
    gap: 0.625rem;
    align-items: flex-end;
  }
  .inntak-skrá-hnappurinn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    color: var(--text-muted);
    cursor: not-allowed;
    opacity: 0.5;
    transition: all var(--transition);
  }
  .inntak-þekja { flex: 1; position: relative; }
  .inntak-textarea {
    width: 100%;
    background: var(--bg-elevated);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-lg);
    padding: 0.625rem 0.875rem;
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 0.9375rem;
    line-height: 1.5;
    resize: none;
    min-height: 40px;
    max-height: 200px;
    overflow-y: auto;
    transition: border-color var(--transition), box-shadow var(--transition);
  }
  .inntak-textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  .inntak-textarea::placeholder { color: var(--text-muted); }
  .inntak-textarea:disabled { opacity: 0.5; cursor: not-allowed; }
  .inntak-senda-hnappurinn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    border-radius: var(--radius-md);
    color: white;
    cursor: pointer;
    border: none;
    transition: all var(--transition);
  }
  .inntak-senda-hnappurinn:hover:not(:disabled) {
    background: var(--accent-light);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px var(--accent-glow-strong);
  }
  .inntak-senda-hnappurinn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
  .inntak-leiðbeiningar {
    font-size: 0.6875rem;
    color: var(--text-muted);
    text-align: center;
  }
  @media (max-width: 640px) {
    .chat-innri { padding: 0 0.75rem; }
    .inntak-sviði { padding: 0.75rem 0.75rem 0.875rem; }
    .boð-lína.ai-boð .boð-bubble,
    .boð-lína.notenda-boð .boð-bubble { max-width: 92%; }
    .chat-til-baka span { display: none; }
    .chat-merki { display: none; }
  }

  /* Sprint 28: K4/K5 — Mobile polish for intake + results */
  @media (max-width: 640px) {
    /* Intake area */
    .intake-section { padding: 1.5rem 1rem 2rem; }
    .tier-toggle { flex-direction: column; gap: .375rem; }
    .tier-btn { padding: .7rem 1rem; font-size: .875rem; }
    .input-wrap { border-radius: .75rem; }
    .textarea-area { padding: .875rem 1rem .75rem; }
    .intake-textarea { font-size: 1rem; min-height: 5rem; }
    .input-toolbar { padding: .625rem 1rem; gap: .5rem; flex-wrap: wrap; }
    .attach-btn { font-size: .8125rem; padding: .4rem .75rem; }
    .file-hint { display: none; }
    .submit-row { padding: .625rem 1rem .875rem; }
    .greina-btn { width: 100%; padding: .7rem 1rem; font-size: .9375rem; }
    .vault-strip { font-size: .8125rem; padding: .625rem .875rem; }
    /* Results on mobile */
    #v7-results { font-size: .875rem; }
    #v7-results > div { padding: .75rem .875rem; border-radius: .625rem; }
    #v7-status { font-size: .8125rem; padding: .625rem .875rem; }
    /* Section header */
    .section-label { font-size: .625rem; }
    .section-title { font-size: 1.375rem; }
    .section-desc { font-size: .875rem; }
    /* Trust strip */
    .trust-grid { gap: .75rem; }
    .glass-card { padding: 1.25rem; }
    .trust-title { font-size: .9375rem; }
    .trust-desc { font-size: .8125rem; }
  }
</style>
"""

# ─── SVG Logo ─────────────────────────────────────────────────────────────────
SVG_LOGO = '''<svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Alvitur logo">
  <path d="M14 2L4 24h6l1.5-4h5l1.5 4h6L14 2zm0 8l2.5 7h-5L14 10z" fill="currentColor" opacity="0.9"/>
  <circle cx="14" cy="7" r="2.5" fill="#6366F1"/>
</svg>'''

# SVG logo fyrir chat haus (hexagon útgáfa)
SVG_LOGO_CHAT = '''<svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="width:24px;height:24px;">
  <path d="M16 2L28.7 9.5V24.5L16 32L3.3 24.5V9.5L16 2Z"
        fill="rgba(99,102,241,0.15)"
        stroke="#6366F1"
        stroke-width="1.5"/>
  <path d="M11 22L16 10L21 22M13 19H19"
        stroke="#818CF8"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"/>
</svg>'''

# ─── Check SVG ────────────────────────────────────────────────────────────────
CHECK_SVG = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
ACCENT_CHECK = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# ─── Nav Script ───────────────────────────────────────────────────────────────
NAV_SCRIPT = """
<script data-version="99">
// Scroll-aware nav
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
}, {passive: true});

// Mobile menu
const menuBtn = document.querySelector('.mobile-menu-btn');
const navLinks = document.querySelector('.nav-links');
if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const isOpen = navLinks.classList.contains('open');
    menuBtn.setAttribute('aria-expanded', isOpen);
    menuBtn.innerHTML = isOpen
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>'
      : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
  });
}

// Intersection Observer for fade-in
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
</script>
"""

# ─── Sprint 44: Frontend Redesign — Light theme ──────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="is">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Alvitur | Örugg skjalagreining og gervigreind á stjórnsýslustigi</title>
  <meta name="description" content="Greindu flókin skjöl og spurningar á sekúndum. Þín gögn, þín stjórn. Engin vistun í trúnaðarham.">
  <meta property="og:title" content="Alvitur | Örugg skjalagreining á stjórnsýslustigi">
  <meta property="og:description" content="Íslensk gervigreindarlausn fyrir stjórnsýslu og fyrirtæki. Þín gögn, þín stjórn.">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600&display=swap">
  <style>
/* Alvitur.is Design System */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-font-smoothing: antialiased; scroll-behavior: smooth; scroll-padding-top: 5rem; }
:root {
  --font-display: 'General Sans', 'Helvetica Neue', sans-serif;
  --font-body: 'Inter', 'Helvetica Neue', sans-serif;
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.75vw, 1.375rem);
  --text-hero: clamp(2.5rem, 1rem + 4vw, 4rem);
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
  --space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem; --space-10: 2.5rem;
  --space-12: 3rem; --space-16: 4rem; --space-20: 5rem;
  --color-bg: #F5F4F0;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-text-muted: #6B6B6B;
  --color-text-faint: #A3A3A3;
  --color-accent: #0A6B6E;
  --color-accent-hover: #085456;
  --color-accent-light: rgba(10, 107, 110, 0.08);
  --color-accent-border: rgba(10, 107, 110, 0.25);
  --color-border: #E2E0DA;
  --color-border-light: #ECEAE5;
  --color-error: #B5364B;
  --color-success: #2D7A3E;
  --radius-sm: 0.375rem; --radius-md: 0.625rem; --radius-lg: 0.875rem; --radius-xl: 1rem;
  --shadow-card: 0 1px 3px rgba(26,26,26,0.04), 0 4px 16px rgba(26,26,26,0.06);
  --shadow-card-hover: 0 2px 8px rgba(26,26,26,0.06), 0 8px 24px rgba(26,26,26,0.08);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --transition-fast: 150ms var(--ease-out);
  --transition-normal: 250ms var(--ease-out);
  --content-max: 680px;
  --content-wide: 960px;
  --nav-height: 3.75rem;
}
body { min-height: 100dvh; line-height: 1.6; font-family: var(--font-body); font-size: var(--text-base); color: var(--color-text); background-color: var(--color-bg); }
h1,h2,h3,h4,h5,h6 { text-wrap: balance; line-height: 1.15; }
p,li { text-wrap: pretty; max-width: 72ch; }
button { cursor: pointer; background: none; border: none; font: inherit; color: inherit; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); }
/* NAV */
.nav { position: fixed; top: 0; left: 0; right: 0; z-index: 50; height: var(--nav-height); background: rgba(245,244,240,0.92); backdrop-filter: blur(12px); border-bottom: 1px solid var(--color-border-light); }
.nav__inner { max-width: var(--content-wide); margin: 0 auto; padding: 0 var(--space-6); height: 100%; display: flex; align-items: center; justify-content: space-between; }
.nav__logo { display: flex; align-items: center; gap: var(--space-2); text-decoration: none; color: var(--color-text); }
.nav__logo-text { font-family: var(--font-display); font-weight: 600; font-size: 1.25rem; letter-spacing: -0.02em; }
.nav__links { display: flex; align-items: center; gap: var(--space-6); }
.nav__link { font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); text-decoration: none; }
.nav__link:hover { color: var(--color-accent); }
/* HERO */
.hero { padding-top: calc(var(--nav-height) + var(--space-16)); padding-bottom: var(--space-12); text-align: center; }
.hero__inner { max-width: var(--content-max); margin: 0 auto; padding: 0 var(--space-6); }
.hero__heading { font-family: var(--font-display); font-size: var(--text-hero); font-weight: 600; letter-spacing: -0.03em; line-height: 1.08; color: var(--color-text); margin-bottom: var(--space-5); }
.hero__subtext { font-size: var(--text-base); color: var(--color-text-muted); line-height: 1.65; max-width: 520px; margin: 0 auto var(--space-8); }
.hero__cta { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; text-decoration: none; border-radius: var(--radius-md); }
.hero__cta:hover { background: var(--color-accent-hover); }
/* INTAKE */
.intake-section { padding: 0 var(--space-6) var(--space-16); }
.intake-card { max-width: var(--content-max); margin: 0 auto; background: var(--color-surface); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); border: 1px solid var(--color-border-light); padding: var(--space-6); }
.intake-card--dragover { border-color: var(--color-accent); border-style: dashed; box-shadow: var(--shadow-card-hover); }
.intake-tabs { display: flex; border-bottom: 1px solid var(--color-border-light); margin-bottom: var(--space-5); }
.intake-tab { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); background: none; border: none; border-bottom: 2px solid transparent; margin-bottom: -1px; cursor: pointer; }
.intake-tab:hover { color: var(--color-text); }
.intake-tab--active { color: var(--color-accent); border-bottom-color: var(--color-accent); font-weight: 600; }
.intake-trust { display: flex; align-items: flex-start; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--color-accent-light); border-radius: var(--radius-md); margin-bottom: var(--space-4); }
.intake-trust p { font-size: var(--text-sm); color: var(--color-accent); line-height: 1.5; }
.intake-textarea { width: 100%; min-height: 120px; padding: var(--space-4); background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-md); font-family: var(--font-body); font-size: var(--text-base); line-height: 1.6; color: var(--color-text); resize: vertical; }
.intake-textarea::placeholder { color: var(--color-text-faint); }
.intake-textarea:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-light); }
.intake-body { margin-bottom: var(--space-4); }
.intake-file-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-4); }
.intake-file-left { display: flex; align-items: center; gap: var(--space-2); }
.intake-file-btn { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: none; cursor: pointer; }
.intake-file-btn:hover { color: var(--color-accent); border-color: var(--color-accent-border); background: var(--color-accent-light); }
.intake-file-hint { font-size: var(--text-xs); color: var(--color-text-faint); }
.intake-attached { display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) var(--space-4); background: var(--color-accent-light); border: 1px solid var(--color-accent-border); border-radius: var(--radius-md); margin-bottom: var(--space-4); }
.intake-attached__name { font-size: var(--text-sm); font-weight: 500; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 240px; }
.intake-attached__size { font-size: var(--text-xs); color: var(--color-text-muted); }
.intake-attached__remove { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: var(--radius-sm); color: var(--color-text-muted); }
.intake-attached__remove:hover { background: rgba(181,54,75,0.1); color: var(--color-error); }
.intake-submit { display: flex; align-items: center; justify-content: center; gap: var(--space-2); width: 100%; padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; border: none; border-radius: var(--radius-md); cursor: pointer; }
.intake-submit:hover { background: var(--color-accent-hover); }
.intake-submit:disabled { opacity: 0.6; cursor: not-allowed; }
@keyframes fadeSlideIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
.spinner { width: 16px; height: 16px; border: 2px solid var(--color-accent-border); border-top-color: var(--color-accent); border-radius: 50%; animation: spin 0.7s linear infinite; }
.intake-status { max-width: var(--content-max); margin: var(--space-4) auto 0; text-align: center; }
.status-message { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border-radius: var(--radius-md); font-size: var(--text-sm); }
.status-message--loading { color: var(--color-accent); background: var(--color-accent-light); }
.status-message--error { color: var(--color-error); background: rgba(181,54,75,0.08); }
.status-message--success { color: var(--color-success); background: rgba(45,122,62,0.08); }
.intake-results { max-width: var(--content-max); margin: var(--space-6) auto 0; }
.results-card { background: var(--color-surface); border: 1px solid var(--color-border-light); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); overflow: hidden; animation: fadeSlideIn 400ms var(--ease-out) both; }
.results-header { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) var(--space-6); border-bottom: 1px solid var(--color-border-light); }
.results-title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; }
.results-badge { display: inline-flex; align-items: center; padding: var(--space-1) var(--space-3); font-size: var(--text-xs); font-weight: 600; color: var(--color-success); background: rgba(45,122,62,0.08); border-radius: var(--radius-sm); }
.results-body { padding: var(--space-6); font-size: var(--text-base); line-height: 1.7; }
.results-body p { margin-bottom: var(--space-4); }
/* TRUST STRIP */
.trust-strip { padding: var(--space-12) var(--space-6) var(--space-8); }
.trust-strip__inner { max-width: var(--content-wide); margin: 0 auto; display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: var(--space-3); }
.trust-strip__item { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-text-faint); }
.trust-strip__dot { color: var(--color-text-faint); font-size: var(--text-xs); }
.trust-strip__link { text-align: center; margin-top: var(--space-3); }
.trust-strip__link a { font-size: var(--text-xs); font-weight: 600; color: var(--color-accent); text-decoration: none; }
/* BETA NOTE */
.beta-note { padding: 0 var(--space-6) var(--space-10); text-align: center; }
.beta-note p { font-size: var(--text-xs); color: var(--color-text-faint); margin: 0 auto; }
/* FOOTER */
.footer { padding: var(--space-8) var(--space-6); border-top: 1px solid var(--color-border-light); }
.footer__inner { max-width: var(--content-wide); margin: 0 auto; text-align: center; }
.footer__copy { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__copy a, .footer__links a { color: var(--color-text-muted); text-decoration: none; }
.footer__copy a:hover, .footer__links a:hover { color: var(--color-accent); }
.footer__links { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__links span { margin: 0 var(--space-2); }
.footer__eea { font-size: var(--text-xs); color: var(--color-text-faint); }
/* SUBPAGE (for build_subpage compatibility) */
.subpage-card { max-width: var(--content-max); margin: calc(var(--nav-height) + var(--space-8)) auto var(--space-8); padding: var(--space-6); background: var(--color-surface); border-radius: var(--radius-xl); box-shadow: var(--shadow-card); border: 1px solid var(--color-border-light); }
.subpage-card h1 { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-4); }
.subpage-card h2 { font-family: var(--font-display); font-size: var(--text-base); font-weight: 600; margin-top: var(--space-6); margin-bottom: var(--space-3); }
.subpage-card p { font-size: var(--text-sm); color: var(--color-text-muted); margin-bottom: var(--space-3); line-height: 1.65; }
.subpage-card a { color: var(--color-accent); }
.legal-date { font-size: var(--text-xs); color: var(--color-text-faint); }
@media (max-width: 640px) {
  :root { --nav-height: 3.25rem; }
  .hero { padding-top: calc(var(--nav-height) + var(--space-10)); padding-bottom: var(--space-8); }
  .intake-card { padding: var(--space-4); }
  .intake-file-row { flex-direction: column; align-items: flex-start; gap: var(--space-2); }
  .trust-strip__inner { flex-direction: column; gap: var(--space-2); }
  .trust-strip__dot { display: none; }
}
  </style>
</head>
<body>
  <a href="#intake-card" class="skip-link">Fara beint í efni</a>
  <nav class="nav" role="navigation" aria-label="Aðalvalmynd">
    <div class="nav__inner">
      <a href="/" class="nav__logo" aria-label="Alvitur forsíða">
        <svg class="nav__logo-mark" viewBox="0 0 28 28" fill="none" aria-hidden="true" width="28" height="28">
          <rect width="28" height="28" rx="6" fill="currentColor" opacity="0.1"/>
          <path d="M7 21L14 7L21 21M10.5 16h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span class="nav__logo-text">Alvitur</span>
      </a>
      <div class="nav__links">
        <a href="/oryggi" class="nav__link">Öryggi</a>
        <a href="#um-alvitur" class="nav__link">Um Alvitur</a>
      </div>
    </div>
  </nav>

  <main id="main-content" tabindex="-1">
    <section class="hero" aria-labelledby="hero-heading">
      <div class="hero__inner">
        <h1 class="hero__heading" id="hero-heading">Greindu flókin skjöl og spurningar á sekúndum.</h1>
        <p class="hero__subtext">Íslensk gervigreindarlausn, byggð fyrir stjórnsýslu og fyrirtæki sem gera ströngustu kröfur um upplýsingaöryggi. <strong>Þín gögn, þín stjórn.</strong></p>
        <a href="#intake-card" class="hero__cta">
          Byrja greiningu
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </a>
      </div>
    </section>

    <section class="intake-section" aria-label="Greiningarsvæði">
      <div class="intake-card" id="intake-card" role="region" aria-label="Inntakssvæði">
        <div class="intake-tabs" role="tablist" aria-label="Greiningarhamur">
          <button class="intake-tab intake-tab--active" id="tab-general" role="tab" aria-selected="true" aria-controls="intake-body" data-mode="general">Almenn greining</button>
          <button class="intake-tab" id="tab-confidential" role="tab" aria-selected="false" aria-controls="intake-body" data-mode="confidential">
            <svg class="intake-tab__lock" viewBox="0 0 14 14" fill="none" aria-hidden="true" width="14" height="14"><rect x="2" y="6" width="10" height="7" rx="1.5" stroke="currentColor" stroke-width="1.25"/><path d="M4.5 6V4.5a2.5 2.5 0 015 0V6" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>
            Trúnaðargreining
          </button>
        </div>

        <div id="trust-statement" class="intake-trust" hidden>
          <svg class="intake-trust__icon" viewBox="0 0 18 18" fill="none" aria-hidden="true" width="18" height="18"><path d="M9 2L3 4.5v5C3 13.1 5.6 16 9 17c3.4-1 6-3.9 6-7.5v-5L9 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          <p>Gögnin þín eyðast sjálfkrafa að vinnslu lokinni. Ekkert rekstrarspor verður til.</p>
        </div>

        <div class="intake-body" id="intake-body">
          <textarea id="query-input" class="intake-textarea" placeholder="Skrifaðu fyrirspurn eða dragðu skjal hingað..." rows="5" aria-label="Fyrirspurn"></textarea>
        </div>

        <div class="intake-file-row">
          <div class="intake-file-left">
            <button class="intake-file-btn" id="file-trigger" type="button" aria-label="Hengja við skjal">
              <svg class="intake-file-btn__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" width="16" height="16"><path d="M3 10V5a5 5 0 0110 0v5.5a3.5 3.5 0 01-7 0V5.5a2 2 0 014 0V10" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/></svg>
              Hengja við PDF
            </button>
            <input type="file" id="file-input" accept=".pdf,.docx,.xlsx" hidden aria-label="Veldu skjal">
            <span id="attached-file" class="intake-attached" hidden aria-live="polite">
              <span class="intake-attached__info">
                <svg class="intake-attached__icon" viewBox="0 0 16 16" fill="none" aria-hidden="true" width="16" height="16"><path d="M4 4h5l3 3v7H4V4z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/><path d="M9 4v3h3" stroke="currentColor" stroke-width="1.25"/></svg>
                <span id="attached-name" class="intake-attached__name"></span>
              </span>
              <span id="attached-size" class="intake-attached__size"></span>
              <button id="remove-file" class="intake-attached__remove" type="button" aria-label="Fjarlægja skjal">
                <svg viewBox="0 0 14 14" fill="none" width="14" height="14"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
            </span>
          </div>
          <span class="intake-file-hint">PDF, Word eða Excel</span>
        </div>

        <button class="intake-submit" id="submit-btn" type="button">
          Greina
          <svg class="intake-submit__arrow" viewBox="0 0 18 18" fill="none" aria-hidden="true" width="18" height="18"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </div>

      <div id="status-area" class="intake-status" aria-live="polite"></div>
      <div id="results-area" class="intake-results" hidden aria-live="polite">
        <div class="results-card">
          <div class="results-header">
            <span class="results-title">Niðurstöður greiningar</span>
            <span class="results-badge">Lokið</span>
          </div>
          <div class="results-body" id="results-body"></div>
        </div>
      </div>
    </section>

    <div class="trust-strip" aria-label="Öryggisupplýsingar">
      <div class="trust-strip__inner">
        <span class="trust-strip__item">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 1L2 3.25v4C2 10.2 4.2 12.75 7 13.5c2.8-.75 5-3.3 5-6.25v-4L7 1z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/></svg>
          Engin þjálfun á þínum gögnum
        </span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">Hýst innan EES</span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">Ekkert vistast í trúnaðarham</span>
        <span class="trust-strip__dot" aria-hidden="true">&middot;</span>
        <span class="trust-strip__item">GDPR &middot; EU AI Act</span>
      </div>
      <div class="trust-strip__link">
        <a href="/oryggi">Sjá öryggisstefnu og gagnaforræði &rarr;</a>
      </div>
    </div>

    <div class="beta-note">
      <p>Alvitur er í prufufasa. Nýjar umbætur birtast reglulega.</p>
    </div>
  </main>

  <footer class="footer" role="contentinfo">
    <div class="footer__inner">
      <p class="footer__copy">&copy; 2026 Orkuskipti ehf &middot; <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
      <p class="footer__links"><a href="/personuvernd">Persónuverndarstefna</a><span>&middot;</span><a href="/skilmalar">Skilmálar</a></p>
      <p class="footer__eea">Gögn unnin innan EES</p>
    </div>
  </footer>

  <script data-version="99">
document.addEventListener('DOMContentLoaded', function() {
  "use strict";

  // ── State ──
  var currentMode = "general";
  var currentFile = null;
  var busy = false;

  // ── DOM refs ──
  var tabGeneral = document.getElementById("tab-general");
  var tabConfidential = document.getElementById("tab-confidential");
  var trustStatement = document.getElementById("trust-statement");
  var queryInput = document.getElementById("query-input");
  var fileTrigger = document.getElementById("file-trigger");
  var fileInput = document.getElementById("file-input");
  var attachedFile = document.getElementById("attached-file");
  var attachedName = document.getElementById("attached-name");
  var attachedSize = document.getElementById("attached-size");
  var removeFileBtn = document.getElementById("remove-file");
  var submitBtn = document.getElementById("submit-btn");
  var statusArea = document.getElementById("status-area");
  var resultsArea = document.getElementById("results-area");
  var resultsBody = document.getElementById("results-body");
  var intakeCard = document.getElementById("intake-card");

  // ── Tab toggle ──
  function setMode(mode) {
    currentMode = mode;
    if (mode === "confidential") {
      tabGeneral.classList.remove("intake-tab--active");
      tabGeneral.setAttribute("aria-selected", "false");
      tabConfidential.classList.add("intake-tab--active");
      tabConfidential.setAttribute("aria-selected", "true");
      trustStatement.hidden = false;
    } else {
      tabConfidential.classList.remove("intake-tab--active");
      tabConfidential.setAttribute("aria-selected", "false");
      tabGeneral.classList.add("intake-tab--active");
      tabGeneral.setAttribute("aria-selected", "true");
      trustStatement.hidden = true;
    }
  }
  tabGeneral.addEventListener("click", function() { setMode("general"); });
  tabConfidential.addEventListener("click", function() { setMode("confidential"); });

  // ── File handling ──
  function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  function attachFile(file) {
    if (!file) return;
    var allowed = [".pdf", ".docx", ".xlsx"];
    var ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (allowed.indexOf(ext) === -1) {
      showStatus("error", "Ógild skráargerð. Styður PDF, Word og Excel.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      showStatus("error", "Skráin er of stór. Hámark 20 MB.");
      return;
    }
    currentFile = file;
    attachedName.textContent = file.name;
    attachedSize.textContent = formatSize(file.size);
    attachedFile.hidden = false;
    fileTrigger.style.display = "none";
    clearStatus();
  }

  function removeFile() {
    currentFile = null;
    fileInput.value = "";
    attachedFile.hidden = true;
    fileTrigger.style.display = "";
  }

  fileTrigger.addEventListener("click", function() { fileInput.click(); });
  fileInput.addEventListener("change", function() {
    if (fileInput.files && fileInput.files[0]) attachFile(fileInput.files[0]);
  });
  removeFileBtn.addEventListener("click", removeFile);

  // ── Drag and drop ──
  intakeCard.addEventListener("dragover", function(e) {
    e.preventDefault();
    intakeCard.classList.add("intake-card--dragover");
  });
  intakeCard.addEventListener("dragleave", function() {
    intakeCard.classList.remove("intake-card--dragover");
  });
  intakeCard.addEventListener("drop", function(e) {
    e.preventDefault();
    intakeCard.classList.remove("intake-card--dragover");
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      attachFile(e.dataTransfer.files[0]);
    }
  });

  // ── Status messages ──
  function showStatus(type, msg) {
    statusArea.innerHTML = '<span class="status-message status-message--' + type + '">' +
      (type === "loading" ? '<span class="spinner"></span>' : '') + msg + '</span>';
  }
  function clearStatus() {
    statusArea.innerHTML = "";
  }

  // ── Start analysis — real API call ──
  function startAnalysis() {
    if (busy) return;
    var query = queryInput.value.trim();
    if (!query && !currentFile) {
      showStatus("error", "Sláðu inn fyrirspurn eða hengdu við skjal.");
      return;
    }

    busy = true;
    submitBtn.disabled = true;
    resultsArea.hidden = true;
    showStatus("loading", "Greining í gangi\u2026");

    var fd = new FormData();
    if (currentFile) fd.append("file", currentFile);
    if (query) fd.append("query", query);

    var ctrl = new AbortController();
    var timeoutId = setTimeout(function() {
      ctrl.abort();
      busy = false;
      submitBtn.disabled = false;
      showStatus("error", "Fyrirspurnin rann út á tíma. Reyndu aftur.");
    }, 180000);
    // 🟢 Sprint 62 Patch H: UX progress hints fyrir löng skjöl
    var hint15 = setTimeout(function(){ showStatus("info", "Greining í gangi..."); }, 15000);
    var hint45 = setTimeout(function(){ showStatus("info", "Stórt skjal — sovereign Qwen3 vinnur, augnablik..."); }, 45000);
    var hint90 = setTimeout(function(){ showStatus("info", "Næstum búið — klárar greininguna..."); }, 90000);
    var _clearHints = function(){ clearTimeout(hint15); clearTimeout(hint45); clearTimeout(hint90); };

    fetch("/api/analyze-document", {
      method: "POST",
      body: fd,
      signal: ctrl.signal
    }).then(function(r) {
      clearTimeout(timeoutId); _clearHints();
      if (!r.ok) {
        return r.json().catch(function() { return {}; }).then(function(d) {
          throw { status: r.status, data: d };
        });
      }
      return r.json();
    }).then(function(d) {
      busy = false;
      submitBtn.disabled = false;
      clearStatus();
      showResults(d);
    }).catch(function(err) {
      clearTimeout(timeoutId); _clearHints();
      busy = false;
      submitBtn.disabled = false;
      if (err && err.name === "AbortError") return;
      if (err && err.status) {
        var d = err.data || {};
        if (err.status === 422) {
          var em = d.error_code === "no_text_extracted"
            ? "Ekki tókst að lesa texta úr skjalinu. Reyndu annað skjal."
            : (d.error || "Villa við úrvinnslu. Reyndu aftur.");
          showStatus("error", em);
          return;
        }
        if (err.status === 413) { showStatus("error", "Skráin er of stór. Hámark 20 MB."); return; }
        if (err.status === 415) { showStatus("error", "Ógild skráargerð."); return; }
        if (err.status === 429) { showStatus("error", "Of margar beiðnir. Reyndu aftur eftir stund."); return; }
        showStatus("error", d.error || "Villa í þjónustu. Reyndu aftur síðar.");
        return;
      }
      showStatus("error", "Tenging mistókst. Athugaðu nettengingu og reyndu aftur.");
    });
  }

  submitBtn.addEventListener("click", startAnalysis);

  // ── Show results ──
  function showResults(d) {
    var html = "";
    // Sprint 63 Fasa 0.3c: robust — accept both keys
    var _txt = d.summary || d.response;
    if (_txt) {
      var lines = _txt.split("\n");
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line) html += "<p>" + escapeHtml(line) + "</p>";
      }
    }
    if (!html && d.success) {
      html = "<pre>" + escapeHtml(JSON.stringify(d, null, 2)) + "</pre>";
    }
    resultsBody.innerHTML = html || "<p>Engar niðurstöður.</p>";
    resultsArea.hidden = false;
    resultsArea.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }
});
  </script>
</body>
</html>"""


# ─── A) Web Chat Fasi 1 — /minarsidur [FJARLÆGT Sprint 18] ────────────────────
# Samþætt úr web_chat_fasi1.py — fullbúið UI með mock svörum
# Sprint 18: build_minarsidur_page() og /minarsidur route commentuð út — vefspjall hreinað
# [FASI-2]: Tengja við MimirCoreV5.process_message() í stað mock falls
# def build_minarsidur_page() -> str:
#     """
#     Smíðar HTML síðuna fyrir vefspjallið á /minarsidur.
#     Notar sömu CSS breytur og forsíðan (dark mode Enterprise hönnun).
#     Fasi 1: Mock svör, engin JWT auðkenning, engin V5 tenging.
#     """
#     return """<!DOCTYPE html>
# <html lang="is">
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width, initial-scale=1.0">
#   <meta name="description" content="Alvitur — Íslenskur AI aðstoðarmaður fyrir skjalagreiningu">
#   <meta name="robots" content="noindex, nofollow">
#   <title>Alvitur — Lokað Gagnaherbergi</title>
#   {SHARED_HEAD}
#   {SHARED_STYLES}
#   <style>
#     /* Yfirskrifa body til fullskjás í spjalli */
#     body {{
#       overflow: hidden;
#       min-height: 100dvh;
#     }}
#   </style>
# </head>
# <body>
# 
#   <!-- Aðgengistengill -->
#   <a href="#spjall-inntak" class="skip-link">Fara beint í inntak</a>
# 
#   <!-- ─── HAUS ─────────────────────────────── -->
#   <header class="chat-haus" role="banner">
#     <a href="/" class="chat-til-baka" aria-label="Til baka á alvitur.is forsíðu">
#       <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
#         <path d="M10 12L6 8l4-4"/>
#       </svg>
#       <span>Til baka</span>
#     </a>
#     <div class="chat-aðskilir" aria-hidden="true"></div>
#     <div class="chat-logo" aria-label="Alvitur">
#       {SVG_LOGO_CHAT}
#       Alvitur
#     </div>
#     <div class="chat-merki" role="status" aria-label="Þjónusta virk">
#       <div class="chat-merki-dot" aria-hidden="true"></div>
#       Lokað Gagnaherbergi
#     </div>
#   </header>
# 
#   <!-- ─── AÐALSVÆÐI ────────────────────────── -->
#   <div class="chat-skipulag">
# 
#     <!-- Spjallsaga -->
#     <main class="chat-saga" id="spjall-saga" role="log" aria-live="polite" aria-label="Spjallsaga" tabindex="0">
#       <div class="chat-innri" id="spjall-innri">
# 
#         <!-- Velkomnarboð (birtist við hleðslu) -->
#         <div class="boð-lína ai-boð" id="velkomin-boð">
#           <div class="boð-merki ai-merki" aria-hidden="true">
#             <svg width="16" height="16" viewBox="0 0 32 32" fill="none">
#               <path d="M16 2L28.7 9.5V24.5L16 32L3.3 24.5V9.5L16 2Z" fill="rgba(99,102,241,0.3)" stroke="#818CF8" stroke-width="1.5"/>
#               <path d="M11 22L16 10L21 22M13 19H19" stroke="#818CF8" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
#             </svg>
#           </div>
#           <div>
#             <div class="boð-bubble">
#               <div class="boð-texti" id="velkomin-texti"></div>
#             </div>
#             <span class="boð-tími" id="velkomin-timi" aria-label="Tímastimpill"></span>
#           </div>
#         </div>
# 
#       </div>
#     </main>
# 
#     <!-- Inntakssvæðið -->
#     <form id="chat-form" class="inntak-sviði" role="region" aria-label="Skilaboðainntak" onsubmit="return false;">
#       <div class="inntak-innri">
#         <div class="inntak-rowr">
#           <!-- Skráarsendir (óvirkur í Fasa 1) -->
#           <button
#             class="inntak-skrá-hnappurinn"
#             disabled
#             aria-label="Hlaða upp skjali (kemur fljótlega)"
#             title="Skráarsendir kemur í Fasa 4"
#           >
#             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
#               <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
#             </svg>
#           </button>
# 
#           <!-- Textasvæðið -->
#           <div class="inntak-þekja">
#             <textarea
#               id="spjall-inntak"
#               class="inntak-textarea"
#               placeholder="Skrifaðu spurninguna þína hér..."
#               rows="1"
#               aria-label="Spjallinntak"
#               aria-multiline="true"
#             ></textarea>
#           </div>
# 
#           <!-- Sendahnappur -->
#           <button
#             id="senda-hnappurinn"
#             class="inntak-senda-hnappurinn"
#             aria-label="Senda skilaboð"
#             onclick="if(typeof handleSend==='function')handleSend();"
#           >
#             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
#               <path d="M22 2L11 13M22 2L15 22 11 13 2 9l20-7z" stroke-linecap="round" stroke-linejoin="round"/>
#             </svg>
#           </button>
#         </div>
#         <p class="inntak-leiðbeiningar">
#           <kbd>Enter</kbd> sendir · <kbd>Shift+Enter</kbd> = nýlína ·
#           <span style="color: var(--accent-light)">Fasi 1 — Mock svör</span>
#         </p>
#       </div>
#     </form>
# 
#   </div>
# 
#   <!-- ─── A) VEFSPJALL JAVASCRIPT ──────────────── -->
#   <script data-version="99">
#   // ================================================================
#   // Alvitur Vefspjall — Fasi 1 (Mock svör)
#   // Sprint 16.4 — samþætt úr web_chat_fasi1.py
#   //
#   // [FASI-2]: Skipta /api/chat kalli út fyrir MimirCoreV5 tengingu
#   // [FASI-3]: Bæta við JWT auðkenningu og lotustjórnun
#   // [FASI-4]: SSE streyming, PDF upphleðsla
#   // ================================================================
# 
#   // ─── Hjálparföll ──────────────────────────────────────────────
#   function currentTime() {{
#     return new Date().toLocaleTimeString('is-IS', {{
#       hour: '2-digit',
#       minute: '2-digit'
#     }});
#   }}
# 
#   // Einföldur Markdown þáttur (Fasi 1 — regex)
#   // [FASI-2]: Skipta út fyrir marked.js CDN
#   function parseMarkdown(texti) {{
#     // Þrífa og varða HTML
#     let html = texti
#       .replace(/&/g, '&amp;')
#       .replace(/</g, '&lt;')
#       .replace(/>/g, '&gt;');
# 
#     // Markdown → HTML umbreytingar (röð skiptir máli)
#     html = html
#       // Kóðablokk (```...```)
#       .replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>')
#       // Inline kóði (`...`)
#       .replace(/`([^`]+)`/g, '<code>$1</code>')
#       // Feitletrað (**...**)
#       .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
#       // Skáletrað (*...*)
#       .replace(/\\*([^*]+)\\*/g, '<em>$1</em>')
#       // Markdown tafla — einföldun
#       .replace(/\\|(.+)\\|/g, (match) => {{
#         const frumur = match.split('|').filter(s => s.trim() !== '');
#         const isSeparator = frumur.every(s => /^[-:\\s]+$/.test(s));
#         if (isSeparator) return '';
#         const td = frumur.map(s => `<td>${{s.trim()}}</td>`).join('');
#         return `<tr>${{td}}</tr>`;
#       }})
#       // Pakka töflurowm
#       .replace(/(<tr>.*<\\/tr>)+/gs, match => {{
#         const rowr = match.match(/<tr>.*?<\\/tr>/gs) || [];
#         if (rowr.length === 0) return match;
#         const haus = rowr[0].replace(/<td>/g, '<th>').replace(/<\\/td>/g, '</th>');
#         const tbody = rowr.slice(1).join('');
#         return `<table><thead>${{haus}}</thead><tbody>${{tbody}}</tbody></table>`;
#       }})
#       // Listi (- atriði)
#       .replace(/^- (.+)$/gm, '<li>$1</li>')
#       .replace(/(<li>.*<\\/li>\\n?)+/gs, match => `<ul>${{match}}</ul>`)
#       // Númeraður listi
#       .replace(/^\\d+\\.(.+)$/gm, '<li>$1</li>')
#       // Tenglar [texti](URL)
#       .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
#       // Línufall → efnisgrein
#       .replace(/\n\n/g, '</p><p>')
#       // Einföldur rowfall
#       .replace(/\n/g, '<br>');
# 
#     // Pakka í efnisgrein ef ekki þegar pakkað
#     if (!html.startsWith('<')) {{
#       html = `<p>${{html}}</p>`;
#     }}
# 
#     return html;
#   }}
# 
#   // ─── Búa til boðarow ──────────────────────────────────────────
#   function createAiMsg(texti, er_hlaðning = false) {{
#     const row = document.createElement('div');
#     row.className = 'boð-lína ai-boð';
# 
#     const merki = document.createElement('div');
#     merki.className = 'boð-merki ai-merki';
#     merki.setAttribute('aria-hidden', 'true');
#     merki.innerHTML = `<svg width="16" height="16" viewBox="0 0 32 32" fill="none">
#       <path d="M16 2L28.7 9.5V24.5L16 32L3.3 24.5V9.5L16 2Z" fill="rgba(99,102,241,0.3)" stroke="#818CF8" stroke-width="1.5"/>
#       <path d="M11 22L16 10L21 22M13 19H19" stroke="#818CF8" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
#     </svg>`;
# 
#     const efni = document.createElement('div');
#     const bubble = document.createElement('div');
#     bubble.className = 'boð-bubble';
# 
#     const msgText = document.createElement('div');
#     msgText.className = 'boð-texti';
# 
#     if (er_hlaðning) {{
#       // Þrír boppandi punktar meðan beðið er
#       msgText.innerHTML = `<div class="hladning-rowr" aria-label="Alvitur er að hugsa...">
#         <div class="hladning-dot"></div>
#         <div class="hladning-dot"></div>
#         <div class="hladning-dot"></div>
#       </div>`;
#     }} else {{
#       msgText.innerHTML = parseMarkdown(texti);
#     }}
# 
#     bubble.appendChild(msgText);
# 
#     const timi = document.createElement('span');
#     timi.className = 'boð-tími';
#     timi.textContent = currentTime();
#     timi.setAttribute('aria-label', `Sent kl. ${{currentTime()}}`);
# 
#     efni.appendChild(bubble);
#     efni.appendChild(timi);
#     row.appendChild(merki);
#     row.appendChild(efni);
# 
#     return {{ row, msgText }};
#   }}
# 
#   function createUserMsg(texti) {{
#     const row = document.createElement('div');
#     row.className = 'boð-lína notenda-boð';
# 
#     const efni = document.createElement('div');
#     const bubble = document.createElement('div');
#     bubble.className = 'boð-bubble';
#     bubble.textContent = texti;
# 
#     const timi = document.createElement('span');
#     timi.className = 'boð-tími';
#     timi.textContent = currentTime();
# 
#     efni.appendChild(bubble);
#     efni.appendChild(timi);
#     row.appendChild(efni);
# 
#     return row;
#   }}
# 
#   // ─── Skruna neðst ──────────────────────────────────────────────
#   function scrollBottom() {{
#     const saga = document.getElementById('spjall-saga');
#     saga.scrollTop = saga.scrollHeight;
#   }}
# 
#   // ─── Senda skilaboð til API ────────────────────────────────────
#   // [FASI-2]: /api/chat kallar á MimirCoreV5
#   async function sendMessage(texti) {{
#     try {{
#       const svar = await fetch('/api/chat', {{
#         method: 'POST',
#         headers: {{ 'Content-Type': 'application/json' }},
#         body: JSON.stringify({{
#           message: texti,
#           user_id: 'web_user_fasi1'  // [FASI-3]: Skipta út fyrir JWT user_id
#         }})
#       }});
# 
#       if (!svar.ok) {{
#         const villa = await svar.json().catch(() => ({{}}));
#         throw new Error(villa.detail || `HTTP villa: ${{svar.status}}`);
#       }}
# 
#       const data = await svar.json();
#       return data.response;
# 
#     }} catch (villa) {{
#       console.error('Spjallvilla:', villa);
#       if (villa.message.includes('429')) {{
#         return 'Þú hefur sent of margar beiðnir. Bíddu smástund og reyndu aftur.';
#       }}
#       return `**Villa kom upp:** ${{villa.message}}\\n\\nReyndu aftur eða hafðu samband við okkur.`;
#     }}
#   }}
# 
#   // ─── Aðalfall: meðhöndla sending ──────────────────────────────
#   let isSending = false;
# 
#   async function handleSend() {{
#     if (isSending) return;
# 
#     const inntak = document.getElementById('spjall-inntak');
#     const texti = inntak.value.trim();
#     if (!texti) return;
# 
#     isSending = true;
#     const sendaHnappur = document.getElementById('senda-hnappurinn');
#     sendaHnappur.disabled = true;
#     inntak.disabled = true;
# 
#     // Birta notendaboð
#     const innri = document.getElementById('spjall-innri');
#     const userRow = createUserMsg(texti);
#     innri.appendChild(userRow);
#     inntak.value = '';
#     inntak.style.height = 'auto';
#     scrollBottom();
# 
#     // Birta hlaðningu
#     const {{ row: hlaðningLína, msgText: hlaðningTexti }} = createAiMsg('', true);
#     innri.appendChild(hlaðningLína);
#     scrollBottom();
# 
#     try {{
#       // Sækja svar frá API
#       const svarTexti = await sendMessage(texti);
# 
#       // Skipta hlaðningu út fyrir raunverulegt svar
#       hlaðningTexti.innerHTML = parseMarkdown(svarTexti);
# 
#     }} catch (villa) {{
#       hlaðningTexti.innerHTML = parseMarkdown('**Villa kom upp.** Reyndu aftur.');
#     }} finally {{
#       isSending = false;
#       sendaHnappur.disabled = false;
#       inntak.disabled = false;
#       inntak.focus();
#       scrollBottom();
#     }}
#   }}
# 
#   // ─── Uppsetning þegar DOM er tilbúið ──────────────────────────
#   document.addEventListener('DOMContentLoaded', function() {{
# 
#     // Birta velkomnarboð með lykilsetningum úr mock svörum
#     const velkomin = `Góðan daginn! Ég er **Alvitur**, íslenskur gervigreindaraðstoðarmaður sérhæfður í skjalagreiningu og lögfræðilegri rannsókn.
# 
# Ég get aðstoðað þig með:
# - Greiningu á **ársreikningum** og fjárhagslegum skjölum
# - Leit og samantekt úr **íslenskum lögum og reglugerðum**
# - Samanburð á **samningum** og lagalegum gögnum
# - **Minnisblöð** og skýrslugerð á sekúndum
# 
# Hvað get ég gert fyrir þig í dag?`;
# 
#     const velkoninTexti = document.getElementById('velkomin-texti');
#     const velkoninTimi = document.getElementById('velkomin-timi');
#     if (velkoninTexti) {{
#       velkoninTexti.innerHTML = parseMarkdown(velkomin);
#     }}
#     if (velkoninTimi) {{
#       velkoninTimi.textContent = currentTime();
#     }}
# 
#     // Stillta inntak og takka
#     const inntak = document.getElementById('spjall-inntak');
#     const sendaHnappur = document.getElementById('senda-hnappurinn');
# 
#     // Virkja senda takka þegar texti er til staðar
#     inntak.addEventListener('input', function() {{
#       const hefurTexta = this.value.trim().length > 0;
#       sendaHnappur.disabled = !hefurTexta || isSending;
# 
#       // Sjálfvirk hæðarstilling á textarea
#       this.style.height = 'auto';
#       this.style.height = Math.min(this.scrollHeight, 200) + 'px';
#     }});
# 
#     // Enter sendir, Shift+Enter brýtur row
#     inntak.addEventListener('keydown', function(e) {{
#       if (e.key === 'Enter' && !e.shiftKey) {{
#         e.preventDefault();
#         if (!sendaHnappur.disabled) {{
#           handleSend();
#         }}
#       }}
#     }});
# 
#     // Smella á senda takka
#     sendaHnappur.addEventListener('click', handleSend);
# 
#     // Form submit (mobile vafrar)
#     const chatForm = document.getElementById('chat-form');
#     if (chatForm) {{
#       chatForm.addEventListener('submit', function(e) {{
#         e.preventDefault();
#         if (!sendaHnappur.disabled) {{
#           handleSend();
#         }}
#       }});
#     }}
# 
#     // Touch event á senda takka (mobile)
#     sendaHnappur.addEventListener('touchend', function(e) {{
#       e.preventDefault();
#       if (!this.disabled) {{
#         handleSend();
#       }}
#     }});
# 
#     // Setja fókus á inntak
#     inntak.focus();
#     scrollBottom();
#   }});
#   </script>
# 
# </body>
# </html>"""
# 
# 
# ─── Mock Checkout ────────────────────────────────────────────────────────────

def build_checkout_page(plan: str, amount: int, user_id: str) -> str:
    plan_names = {
        "brons": "Brons",
        "silfur": "Silfur",
        "gull": "Gull",
        "platina": "Platína",
    }
    plan_display = plan_names.get(plan.lower(), plan.capitalize())
    amount_display = f"{amount:,}".replace(",", ".") + " kr" if amount > 0 else "Frítt"

    return """<!DOCTYPE html>
<html lang="is">
<head>
  <title>Greiðsla — {plan_display} — Alvitur</title>
  {SHARED_HEAD}
  {SHARED_STYLES}
</head>
<body>
  <div class="subpage-center">
    <div class="subpage-card">
      <div style="font-size: 2rem; margin-bottom: 0.5rem;">💳</div>
      <h1>Greiðsla</h1>
      <p>Þetta er prófunargreiðslusíða (mock checkout) — engin raunveruleg greiðsla fer fram.</p>

      <div class="checkout-summary">
        <div class="checkout-row">
          <span class="label">Áskrift</span>
          <span class="value">{plan_display}</span>
        </div>
        <div class="checkout-row">
          <span class="label">Notandi</span>
          <span class="value" style="font-family: var(--font-mono); font-size: 0.8125rem;">{user_id}</span>
        </div>
        <div class="checkout-row checkout-total">
          <span class="label">Samtals</span>
          <span class="value">{amount_display} / mán.</span>
        </div>
      </div>

      <form action="/api/webhook/mock_success" method="POST">
        <input type="hidden" name="plan" value="{plan}">
        <input type="hidden" name="amount" value="{amount}">
        <input type="hidden" name="user_id" value="{user_id}">
        <input class="input-field" type="text" placeholder="Nafn á korti" autocomplete="cc-name" required>
        <input class="input-field" type="text" placeholder="0000 0000 0000 0000" autocomplete="cc-number" required>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
          <input class="input-field" type="text" placeholder="MM/ÁÁ" autocomplete="cc-exp" required>
          <input class="input-field" type="text" placeholder="CVC" autocomplete="cc-csc" required>
        </div>
        <button type="submit" class="btn btn-primary btn-lg" style="width: 100%; justify-content: center; margin-top: 0.75rem;">
          Staðfesta greiðslu (próf)
        </button>
      </form>

      <a href="/" class="btn btn-secondary" style="width: 100%; justify-content: center; margin-top: 0.75rem;">← Hætta við</a>
    </div>
  </div>
</body>
</html>"""


# ─── Mock Success ─────────────────────────────────────────────────────────────

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

@app.get("/", response_class=HTMLResponse)
async def home():
    """Forsíða — þjónar index.html úr disk."""
    import os
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=HTML_PAGE)


def build_subpage(titill: str, texti: str) -> str:
    """Sprint 21: Hjálparfall — smíðar einföldu undirsíðu með sama grunn og forsíðan."""
    return HTML_PAGE.replace(
        '<main id="main-content" tabindex="-1">',
        f'<main id="main-content" tabindex="-1"><div class="subpage-card"><h1>{titill}</h1>{texti}</div>',
    ).replace(
        '</main>',
        '</main>',
        1
    )


# ─── Sprint 21: Persónuvernd og Skilmálar ─────────────────────────────

@app.get("/personuvernd", response_class=HTMLResponse)
async def personuvernd():
    """Persónuverndarstefna — Sprint 21, lagatexti frá Aðal & Sigvalda."""
    page = build_subpage(
        titill="Persónuverndarstefna Alviturs",
        texti="""
        <p class="legal-date">Síðast uppfært: 6. apríl 2026</p>
        <p>Hjá Alvitri byggjum við allar okkar lausnir á einni meginreglu: <strong>Þín gögn eru þín, og aðeins þín.</strong> Við skiljum að upplýsingarðu sem þú treystir okkur fyrir, sem greiningarvél fyrir stjórnsýslu og atvinnulífið, eru oft afar viðkvæmar.</p>

        <h2>1. Engin geymsla gagna (Zero-Retention Policy)</h2>
        <p>Þegar þú nýtir skjalagreiningarvél Alviturs (Alvitur Analyze) til að vinna úr skjölum (svo sem PDF, Word eða texta), eru gögnin aðeins unnin í dulkóðuðu vinnsluminni á meðan greining stendur yfir. Um leið og niðurstaða hefur verið afhent, er frumgögnunum tafarlaust eytt af netþjónum okkar. Við geymum aldrei skjöl þín nema beinlínis sé óskað eftir því í lokuðum Enterprise-samningum um varðveislu gagna.</p>

        <h2>2. Engin þjálfun á þínum gögnum (No-Training Policy)</h2>
        <p>Við notum gögn viðskiptavina okkar <strong>ALDREI</strong> til að þjálfa okkar eigin gervigreindarlíkön, né leyfum við þriðja aðila að gera slíkt. Þegar Alvitur nýtir stór erlend API líkön í gegnum bakenda okkar, tryggja “Zero-Data” API-samningar við þá þjónustuaðila að engin inntaksgögn eru notuð í neins konar þjálfunarskyni.</p>

        <h2>3. Gagnaflutningur og dulkóðun</h2>
        <p>Öll samskipti milli þín og netþjóna okkar fara fram bak við lokaða “Zero-Trust” innviði (Cloudflare Tunnels) með fullkominni TLS 1.3 dulkóðun. Engin kerfi okkar eru opin beint út á internetið.</p>

        <p>Fyrir fyrirspurnir varðandi meðferð gagna, eða til að nýta rétt þinn til að gleymast samkvæmt persónuverndarlögum (GDPR), vinsamlegast hafið samband á <a href="mailto:info@alvitur.is">info@alvitur.is</a>.</p>
        """
    )
    return HTMLResponse(content=page)


@app.get("/skilmalar", response_class=HTMLResponse)
async def skilmalar():
    """Notkunarskilmálar — Sprint 21, lagatexti frá Aðal & Sigvalda."""
    page = build_subpage(
        titill="Notkunarskilmálar Alvitur.is",
        texti="""
        <p class="legal-date">Síðast uppfært: 6. apríl 2026</p>
        <p>Með þ ví að heimsækja eða nota þ jónustu Alvitur.is samþykkir þú eftirfarandi skilmála. Alvitur er ætlað sem B2B og B2G greiningartól, hannað til vinnslu gagna, skjala og texta.</p>

        <h2>1. Takmörkun ábyrgðar</h2>
        <p>Alvitur beitir háþróuðum gervigreindarlíkönum til að greina gögn og draga saman samhengi. Notandi samþykkir og gerir sér grein fyrir því að gervigreind er hugbúnaður sem byggir á líkindareikningi og getur sætt svokölluðum “ofskynjunum” (hallucinations) eða rangtúlkunum.</p>
        <p>Allar niðurstöður frá Alvitri eru <strong>EINGÖNGU</strong> til stuðnings við ákvarðanaatöku. Alvitur getur aldrei komið í stað formlegrar faglegar, lögfræðilegrar, læknisfræðilegrar eða fjárhagslegrar ráðgjafar. Notandi ber einn og alfarið alla ábyrgð á því að yfirfara og staðfesta upplýsingar áður en þær eru nýttar. Alvitur.is ehf. ber enga fjárhagslega eða lagalega ábyrgð á beinni eða óbeinni tjóni sem kann að hljótast af notkun þjónustunnar.</p>

        <h2>2. Uppruni gagna og höfundarréttur</h2>
        <p>Notandi ábyrgist að hann hafi fullan og lögmætan rétt til að hlaða upp og vinna með þau gögn sem hann setur í kerfi Alviturs.</p>

        <h2>3. Umgengni og misnotkun</h2>
        <p>Það er með öllu óheimilt að reyna að afhjúpa eða bakfæra (reverse engineer) kerfisarkitektúr Alviturs. Óheimilt er að beita árásum eða inngripum (svo sem “Prompt Injection”) á gervigreindina eða nýta API lykla okkar utan viðskiptasamninga. Slík brot varða umsvifalausri lokun reiknings og hugsanlegum skaðabótakröfum.</p>

        <p>Spurningar: <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
        """
    )
    return HTMLResponse(content=page)


# @app.get("/minarsidur", response_class=HTMLResponse)
# async def minarsidur():
#     """A) Web Chat Fasi 1 — v1 minimal (sér .js skrá, engin inline JS)"""
#     html_path = "/workspace/mimir_net/static/minarsidur_v1.html"
#     try:
#         with open(html_path, "r", encoding="utf-8") as f:
#             return HTMLResponse(content=f.read())
#     except FileNotFoundError:
#         return HTMLResponse(content=build_minarsidur_page())
# 


@app.get("/api/health")
async def health():
    """Heilsufarsskoðun — notað af monitoring og load balancer."""
    return JSONResponse(content={
        "status": "ok",
        "version": "sprint63-track-b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fasi": "production",
    })

@app.get("/api/diagnostics")
async def diagnostics():
    """Sprint 63 Track A5 + B3: Diagnostics — stöðu leiða og umhverfis."""
    import os as _os_d
    import time as _time_d
    _key = _os_d.environ.get("OPENROUTER_API_KEY", "")
    leid_a_enabled = bool(_key and len(_key) > 10 and not _key.startswith("sk-or-v1-BAD"))
    # Track B3: vLLM er á port 8002 (ekki 8001 sem var hardcoded default)
    _sovereign_url = _os_d.environ.get("SOVEREIGN_URL", "http://localhost:8002/v1/chat/completions")
    # Track B3: env flag + port
    _env_flag = _os_d.environ.get("ALVITUR_ENV", "prod")
    _port = int(_os_d.environ.get("ALVITUR_PORT", "8000"))
    try:
        uptime = int(_time_d.time() - _SERVER_START_TIME)
    except NameError:
        uptime = -1
    return JSONResponse(content={
        "status": "ok",
        "version": "sprint63-track-b",
        "env": _env_flag,
        "port": _port,
        "leid_a_enabled": leid_a_enabled,
        "leid_a_key_length": len(_key) if _key else 0,
        "leid_b_enabled": bool(_sovereign_url),
        "leid_b_url": _sovereign_url,
        "uptime_seconds": uptime,
        "loaded_env": bool(_key),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ─── Sprint 58+59: MCP Tools Endpoints ─────────────────────────────────────────

@app.get("/api/tools")
async def tools_list():
    """
    Sprint 59: Skilar lista af öllum tiltækum tools.
    MCP-samhæft — notað af MCP clients og /api/tools wiring.
    """
    from interfaces.mcp_server import mcp_list_tools
    tools = await mcp_list_tools()
    return JSONResponse(content={"success": True, "tools": tools, "count": len(tools)})


@app.post("/api/tools/{tool_name}")
async def tools_call(tool_name: str, request: Request):
    """
    Sprint 59: Kallar á tool með gefnum arguments.
    Body: JSON með arguments fyrir tool.
    Skilar niðurstöðu frá tool.
    """
    from interfaces.mcp_server import mcp_call_tool
    try:
        body = await request.json()
    except Exception:
        body = {}
    result = await mcp_call_tool(tool_name, body)
    status = 200 if result.get("success") else 404 if "ekki til" in result.get("error", "") else 502
    return JSONResponse(content=result, status_code=status)


# ─── Sprint 21: PDF Analyze Endpoint ──────────────────────────────────────────────

# ── Sprint 28: K1/K2 — .docx and .xlsx parsers ───────────────────────────────
MAX_DOC_SIZE = 20 * 1024 * 1024  # 20 MB (same as PDF)

MAGIC_BYTES = {
    b'%PDF': 'pdf',
    b'PK\x03\x04': 'office',  # .docx and .xlsx are ZIP-based Office formats
}

def _detect_filetype(data: bytes, filename: str) -> str:
    """Return 'pdf', 'docx', 'xlsx', or raise HTTPException."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    header = data[:4]
    if header == b'%PDF':
        if ext != 'pdf':
            raise HTTPException(status_code=415,
                detail="Skráin er merkt sem PDF en innihald stemmir ekki.")
        return 'pdf'
    if header[:2] == b'PK':
        if ext == 'docx':
            return 'docx'
        if ext == 'xlsx':
            return 'xlsx'
        raise HTTPException(status_code=415,
            detail="Office skjal þekkt en skráarending er óþêkkt. Sendu .docx eða .xlsx.")
    raise HTTPException(status_code=415,
        detail="Skráargerð ekki stuðd. Styður PDF, Word (.docx) og Excel (.xlsx).")


def _parse_docx(data: bytes) -> tuple[int, list[str]]:
    """Extract text from .docx. Returns (page_estimate, text_parts)."""
    from docx import Document
    import io
    doc = Document(io.BytesIO(data))
    parts = []
    for i, para in enumerate(doc.paragraphs):
        t = para.text.strip()
        if t:
            parts.append(t)
    # Estimate pages: ~3000 chars per page
    total_chars = sum(len(p) for p in parts)
    page_estimate = max(1, total_chars // 3000)
    return page_estimate, parts


def _parse_xlsx(data: bytes) -> tuple[int, list[str]]:
    """Extract text from .xlsx. Returns (sheet_count, text_parts)."""
    import openpyxl, io
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    parts = []
    sheet_count = len(wb.sheetnames)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows_text = []
        row_count = 0
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None and str(c).strip()]
            if cells:
                rows_text.append(" | ".join(cells))
                row_count += 1
            if row_count >= 500:  # cap at 500 rows per sheet
                rows_text.append("[... fleiri raðir ...]")
                break
        if rows_text:
            parts.append(f"[Blað: {sheet_name}]\n" + "\n".join(rows_text))
    wb.close()
    return sheet_count, parts

# ─────────────────────────────────────────────────────────────────────────────
# ─ Sprint 27: S4 Wallet Circuit Breaker ───────────────────────────────────
WALLET_MIN_USD       = float(os.environ.get("WALLET_MIN_USD", "5.0"))
WALLET_MIN_VAULT_USD = float(os.environ.get("WALLET_MIN_VAULT_USD", "10.0"))

# PLG quota tracker (IP-based, in-memory)
_quota_tracker_chat: dict = {}  # /api/chat quota per IP
_quota_tracker_doc: dict = {}   # /api/analyze-document quota per IP
FREE_QUOTA = 5



# -- Sprint 66 pre-A hotfix: persist _beta_tracker across restarts --
import json as _json_bt
import os as _os_bt
import time as _time_bt
from pathlib import Path as _Path_bt

_BETA_TRACKER_FILE = _Path_bt(_os_bt.getenv("BETA_TRACKER_PATH", "data/beta_tracker.json"))

def _load_beta_tracker_from_disk() -> dict:
    try:
        if not _BETA_TRACKER_FILE.exists():
            return {}
        raw = _json_bt.loads(_BETA_TRACKER_FILE.read_text(encoding="utf-8"))
        now = _time_bt.time()
        # TODO(S66-A): replace with BETA_DURATION_SEC module const (defined below)
        _DUR = int(_os_bt.getenv("BETA_DURATION_SEC_OVERRIDE", 7 * 24 * 3600))
        return {ip: float(ts) for ip, ts in raw.items() if now - float(ts) <= _DUR}
    except Exception as e:
        try:
            logger.warning(f"[BETA] load failed: {type(e).__name__}: {e}")
        except Exception:
            pass
        return {}

def _save_beta_tracker_to_disk(tracker: dict) -> None:
    try:
        _BETA_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _BETA_TRACKER_FILE.with_suffix(".tmp")
        tmp.write_text(_json_bt.dumps(tracker, indent=2), encoding="utf-8")
        tmp.replace(_BETA_TRACKER_FILE)
    except Exception as e:
        try:
            logger.warning(f"[BETA] save failed: {type(e).__name__}: {e}")
        except Exception:
            pass
# -- /persist helpers --

# ── Sprint 62: Beta tracker ──
# Beta-tier via human phrase in chat: "Sigvaldi sendi mig" (7-day renewable)
_beta_tracker: dict[str, float] = {}   # IP → promotion_timestamp (epoch sec)
BETA_DURATION_SEC = 7 * 24 * 3600      # 7 dagar
BETA_FRASAR = (
    "sigvaldi sendi mig",
    "ég er beta notandi",
    "beta aðgangur",
    "beta adgangur",
)

def _er_beta_fras(text: str) -> bool:
    """Satt ef notendatexti inniheldur einhvern viðurkenndan beta-frasa."""
    if not text:
        return False
    lower = text.lower()
    return any(fras in lower for fras in BETA_FRASAR)

def _er_beta_ip(ip: str) -> bool:
    """Satt ef IP er í beta-tier (innan 7 daga frá promotion)."""
    import time as _t
    ts = _beta_tracker.get(ip)
    if ts is None:
        return False
    if _t.time() - ts > BETA_DURATION_SEC:
        _beta_tracker.pop(ip, None)
        return False
    return True

def _promota_beta(ip: str) -> None:
    """Setur IP í beta-tier núna (eða endurnýjar)."""
    import time as _t
    _beta_tracker[ip] = _t.time()
    _save_beta_tracker_to_disk(_beta_tracker)
# ── /Sprint 62 Beta tracker ──
_beta_tracker.update(_load_beta_tracker_from_disk())
_wallet_cache: dict  = {"balance": None, "ts": 0.0}
_WALLET_TTL          = 120

def _get_openrouter_balance():
    import time as _t, requests as _rq
    now = _t.time()
    if _wallet_cache["balance"] is not None and now - _wallet_cache["ts"] < _WALLET_TTL:
        return _wallet_cache["balance"]
    try:
        _k = os.environ.get("OPENROUTER_API_KEY", "")
        r = _rq.get("https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {_k}"}, timeout=5)
        if r.status_code == 200:
            d = r.json().get("data", {})
            limit = d.get("limit")
            if limit is not None:
                bal = round(float(limit) - float(d.get("usage") or 0), 4)
            else:
                bal = 100.0
            _wallet_cache["balance"] = bal
            _wallet_cache["ts"] = now
            return bal
    except Exception:
        pass
    return None

def _wallet_preflight(is_vault=False):
    bal = _get_openrouter_balance()
    if bal is None: return
    threshold = WALLET_MIN_VAULT_USD if is_vault else WALLET_MIN_USD
    if bal < threshold:
        logger.warning(f"Wallet circuit breaker: balance=${bal:.2f} < ${threshold:.2f}")
        raise HTTPException(status_code=503,
            detail="Þ jónustan er tímabundið ótilðæk. Reyndu aftur eftir augnablik.")

# ───────────────────────────────────────────────────────────
SECURE_DOCS_DIR = Path("/workspace/mimir_net/secure_docs")
SECURE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
MAX_PDF_SIZE = 20 * 1024 * 1024  # Sprint 27 S2: raised to 20 MB



def _log_intent(endpoint: str, query, filename, file_size, tier) -> None:
    """Sprint 64 B2-V2: observability hook. NEVER raises."""
    if not _INTENT_AVAILABLE or _classify_intent is None:
        return
    try:
        ir = _classify_intent(query=query, filename=filename,
                              file_size=file_size, tier=tier)
        logger.info(
            f"[INTENT] endpoint={endpoint} domain={ir.domain} "
            f"depth={ir.reasoning_depth} conf={ir.confidence_score:.2f} "
            f"sens={ir.sensitivity} adapter={ir.adapter_hint} "
            f"src={ir.source_hint}"
        )
    except Exception as _ie:
        logger.warning(f"[INTENT] classify failed on {endpoint}: {type(_ie).__name__}: {_ie}")

@app.post("/api/analyze-document")
async def analyze_document(request: Request, file: Optional[UploadFile] = File(None), query: Optional[str] = Form(None)):
    """
    Sprint 21 — PDF Analyze Endpoint (Lag 1).
    Tekur við PDF skrá, les texta með PyMuPDF og búr til grófótta greiningu.
    Zero-Data: Skrá er eyð um leið og vinnslu ljúkur.
    Sprint 43b: query parameter wired from multipart form data.
    Sprint 43c: file optional — text-only queries fall back to direct LLM call.
    """

    # ── Sprint 43c: text-only fallback ──────────────────────────────
    _tier_hdr = request.headers.get("X-Alvitur-Tier", "general").lower().strip() if request else "general"
    _llm_model = _MODEL_LEIDA_B if _tier_hdr == "vault" else _MODEL_LEIDA_A
    if file is None or file.filename == "":
        if not query or not query.strip():
            return JSONResponse(status_code=422, content={
                "error_code": "empty_prompt",
                "detail": "Vinsamlegast skrifaðu fyrirspurn eða hladdu upp skjali.",
            })
        # Sprint 46 Phase 1b: quota check á text-only path (var vantar)
        import hashlib as _hl
        _master_key_txt = os.environ.get("ALVITUR_MASTER_KEY_HASH", "")
        _req_key_txt = request.headers.get("X-Master-Key", "") if request else ""
        _is_admin_txt = bool(_master_key_txt and _req_key_txt and _hl.sha256(_req_key_txt.encode()).hexdigest() == _master_key_txt)
        _client_ip_txt = (
            request.headers.get("CF-Connecting-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        # ── Sprint 64 A1: Beta check á text-only path (var vantar) ──
        # Speglarar logic í /api/chat (line ~3593) og analyze-document file-path (line ~3294)
        if _er_beta_fras(query or ""):
            _promota_beta(_client_ip_txt)
            logger.info(f"[BETA] {_client_ip_txt} promotaður í beta-tier (7d) via text-only")
        _is_beta_txt = _er_beta_ip(_client_ip_txt)
        # ── /Sprint 64 A1 beta check ──
        _log_intent("analyze-document/text-only", query, None, None, _tier_hdr)
        _quota_count_txt = _quota_tracker_doc.get(_client_ip_txt, 0) + 1
        if not _is_admin_txt and not _is_beta_txt:
            _quota_tracker_doc[_client_ip_txt] = _quota_count_txt
        if _quota_count_txt > FREE_QUOTA and not _is_admin_txt and not _is_beta_txt:
            return JSONResponse(status_code=403, content={
                "success": False,
                "error": "Ókeypis prufutími er liðinn.",
                "error_code": "quota_exceeded",
                "upgrade_required": True,
                "upgrade_url": "/askrift",
                "message": "Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.",
            })

        # Text-only path: send query directly to LLM (async — Sprint 46 Phase 1b)
        import os as _os
        import httpx as _httpx
        from datetime import datetime as _dt, timezone as _tz
        _key = _os.environ.get("OPENROUTER_API_KEY", "")
        _tier = _tier_hdr
        _summary = None
        # 🟢 Sprint 62 Patch E v2: no-key → sovereign Leið B strax (skip OpenRouter entirely)
        if not _key and _tier_hdr != "vault":
            logger.warning("[ALVITUR] Sprint62E NO-KEY → sovereign fallback á Leið B")
            try:
                async with _VAULT_SEMAPHORE_WS:
                    _summary, _model_used, _usage = await _call_leid_b((query or "").strip())
            except Exception as _fe:
                logger.error(f"[ALVITUR] Sprint62E exc: {type(_fe).__name__}: {_fe}")
                _summary = None
            if _summary is None:
                return JSONResponse(status_code=503, content={
                    "error_code": "sovereign_unavailable",
                    "detail": "Staðbundin gervigreind er að ræsast. Reyndu eftir andartak."})
            logger.info(f"[ALVITUR] Sprint62E sovereign OK model={_model_used}")
            return JSONResponse(status_code=200, content={
                "success": True, "summary": _summary, "mode": "text-only",
                "pipeline_source": f"sovereign_nokey_{_model_used}", "model": _model_used})
        if _key:
            try:
                _now_str = _dt.now(_tz.utc).strftime("%Y-%m-%d %H:%M UTC")
                # Sprint 47: Domain classification + specialist prompt
                # Sprint 60c: None guard + honesty instruction
                from interfaces.specialist_prompts import get_specialist_prompt as _get_prompt
                from interfaces.skills.classify import ClassifySkill as _ClsSkill
                try:
                    _domain_txt = await _ClsSkill().run((query or "").strip() or "general", tier=_tier_hdr)
                except Exception:
                    _domain_txt = "general"
                _domain_txt = _domain_txt or "general"
                _honesty = (
                    "\n\nMikilvægt: Ef þú finnur ekki nógu nákvæmar upplýsingar í skjalinu "
                    "til að svara spurningunni, segjum notandanum það beint og bjóðum upp á "
                    "framhaldsspurningu. Búðu ALDREI til upplýsingar sem eru ekki í skjalinu."
                )
                _system_prompt = _get_prompt(_domain_txt, _now_str) + _honesty
                logger.info(f"[ALVITUR] Sprint61 text-only tier={_tier} domain={_domain_txt}")
                _pipeline_source_txt = "unknown"
                if _tier == "vault":
                    from interfaces.config import VAULT_MAX_INPUT_TOKENS as _vmax
                    if _estimate_tokens(query or "") > _vmax:
                        return JSONResponse(status_code=413, content={
                            "error_code": "vault_input_too_large",
                            "detail": "Fyrirspurn er of stór fyrir Vault tier (max 8000 tokens). Styttu textann."})
                    async with _VAULT_SEMAPHORE_WS:
                        _summary, _model_used, _usage = await _call_leid_b(query.strip())
                    if _summary is None:
                        return JSONResponse(status_code=503, content={
                            "error_code": "vault_local_unavailable",
                            "detail": "Trúnaðarþjónusta tímabundið ekki tiltæk. Local AI module er að ræsast — reyndu aftur eftir 1 mínútu."})
                    _pipeline_source_txt = f"local_vllm_{_model_used}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    logger.info(f"[ALVITUR] leid_b sovereign tokens in={_in_tok} out={_out_tok}")
                else:
                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, query.strip())
                    if _summary is None:
                        logger.warning("[ALVITUR] Sprint62C text-only: Leið A None, reyni fallback á Leið B")
                        try:
                            async with _VAULT_SEMAPHORE_WS:
                                _summary, _model_used, _usage = await _call_leid_b(query.strip())
                        except Exception as _fe:
                            logger.error(f"[ALVITUR] Sprint62C fallback exc: {type(_fe).__name__}: {_fe}")
                            _summary = None
                        if _summary is None:
                            return JSONResponse(status_code=503, content={
                                "error_code": "both_pipelines_unavailable",
                                "detail": "Þjónusta tímabundið ekki aðgengileg. Reyndu eftir augnablik."})
                        _pipeline_source_txt = f"fallback_local_{_model_used}"
                        logger.info(f"[ALVITUR] Sprint62C fallback OK: model={_model_used}")
                    else:
                        _pipeline_source_txt = f"openrouter_{_model_used.split('/')[-1]}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    _cost = (_in_tok * 0.15 + _out_tok * 0.60) / 1_000_000 if "gpt-4o-mini" in _model_used else (_in_tok * 3.00 + _out_tok * 15.00) / 1_000_000 if "claude-sonnet" in _model_used else 0.0
                    logger.info("[ALVITUR] token_obs pipeline=text_query model=%s tier=%s in=%d out=%d cost=%.6f", _model_used, _tier, _in_tok, _out_tok, _cost)
                    try:
                        # from interfaces.chat_routes import _polish as _polish_fn_txt
                        _summary = await _polish_fn_txt(_summary, _key)
                    except Exception as _pe:
                        logger.warning(f"[ALVITUR] polish failed (non-fatal): {_pe}")
            except Exception as _e:
                logger.error(f"[ALVITUR] text-only pipeline exc: {type(_e).__name__}: {_e}")
                _summary = None
                _domain_txt = "general"
                _pipeline_source_txt = "error"
        if _summary is None:
            # Sprint 62 Patch C: Final safety net — both pipelines down
            return JSONResponse(status_code=503, content={
                "error_code": "service_unavailable",
                "detail": "Greiningar þjónusta tímabundið ekki aðgengileg. Reyndu aftur eftir andartak.",
            })
        return JSONResponse(content={
            "success": True,
            "filename": None,
            "sidur": 0,
            "zero_data": True,
            "tier": _tier,
            "query": query.strip(),
            "response": _summary,
            "domain": _domain_txt,
            "citations": [],
            "found": True,
            "status": "ready_for_analysis",
            "pipeline_source": _pipeline_source_txt if "_pipeline_source_txt" in dir() else "unknown",
        })

    import fitz  # PyMuPDF

    # — 1. Staðfesta skrártegund —
    _ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if _ext not in ("pdf", "docx", "xlsx"):
        raise HTTPException(status_code=400, detail="Skráargerð ekki stuð. Sendu PDF, Word eða Excel.")

    # S2: Stream size check before full read
    _cl = None
    if hasattr(file, "headers") and file.headers:
        _cl = file.headers.get("content-length")
    if _cl and int(_cl) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413,
            detail="Skjalið er yfir 20 MB — minnkaðu eða veldu annað.")
    efni = await file.read(MAX_PDF_SIZE + 1)
    if len(efni) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413,
            detail="Skjalið er yfir 20 MB — minnkaðu eða veldu annað.")

    # K1/K2/S3: Filetype detection (magic bytes + extension)
    _filetype = _detect_filetype(efni, file.filename)


    # S4: Wallet circuit breaker
    _tier = request.headers.get("X-Alvitur-Tier", "general").lower().strip() if request else "general"
    _is_vault = (_tier == "vault")
    _wallet_preflight(is_vault=_is_vault)

    # PLG quota check — master key bypass
    _master_key = os.environ.get("ALVITUR_MASTER_KEY_HASH", "")
    _req_key = request.headers.get("X-Master-Key", "") if request else ""
    import hashlib as _hl
    _is_admin = bool(_master_key and _req_key and _hl.sha256(_req_key.encode()).hexdigest() == _master_key)
    _client_ip = (request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "unknown"))
    # Sprint 62 Patch A.1: define _is_beta early (was defined 240 lines later, causing NameError)
    try:
        _is_beta = _er_beta_ip(_client_ip)
    except Exception:
        _is_beta = False
    try:
        _fn = file.filename if file else None
        _fsize = getattr(file, "size", None) if file else None
    except Exception:
        _fn, _fsize = None, None
    _log_intent("analyze-document/file", query, _fn, _fsize,
                request.headers.get("X-Alvitur-Tier", "general") if request else "general")
    _quota_count = _quota_tracker_doc.get(_client_ip, 0) + 1
    if not _is_admin:
        _quota_tracker_doc[_client_ip] = _quota_count
    if _quota_count > FREE_QUOTA and not _is_admin and not _is_beta:
        return JSONResponse(status_code=403, content={
            "success": False,
            "error": "Ókeypis prufutími er liðinn.",
            "error_code": "quota_exceeded",
            "upgrade_required": True,
            "upgrade_url": "/askrift",
            "message": "Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.",
        })

    # PLG warning
    _quota_warning = None
    if _quota_count == 4 and not _is_admin:
        _quota_warning = "Þú hefur 1 beiðni eftir af 5 ókeypis beiðnum."
    elif _quota_count == 5 and not _is_admin:
        _quota_warning = "Þetta er þín síðasta ókeypis beiðni. Uppfærðu til að halda áfram."

    # S5+S6: Unified Parser (Office + PDF)
    # Office files (XLSX/DOCX)
    if _filetype in ('xlsx', 'docx'):
        import io
        try:
            if _filetype == 'xlsx':
                # Sprint 62 Patch B: Pandas pre-processor (Reiknivélar-Agent).
                # Returns markdown with real computed sums so LLM doesn't hallucinate.
                try:
                    from interfaces.excel_preprocessor import preprocess_excel as _prep_xlsx
                    heildartexti = _prep_xlsx(efni)
                    sidur = 1
                    logger.info(f"[ALVITUR] Sprint62b xlsx preprocessed via pandas, {len(heildartexti)} chars")
                except Exception as _xe:
                    logger.warning(f"[ALVITUR] pandas preprocess failed, fallback to openpyxl flat: {type(_xe).__name__}: {_xe}")
                    import openpyxl
                    wb = openpyxl.load_workbook(io.BytesIO(efni), read_only=True, data_only=True)
                    txt = []
                    for ws in wb.worksheets:
                        for row in ws.iter_rows(values_only=True):
                            clean = [str(c) if c is not None else "" for c in row]
                            line = " | ".join(v for v in clean if v.strip())
                            if line: txt.append(line)
                    heildartexti = "\n".join(txt)
                    sidur = len(wb.worksheets)
            elif _filetype == 'docx':
                from docx import Document
                doc = Document(io.BytesIO(efni))
                heildartexti = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                sidur = len(doc.paragraphs)
        except Exception as e:
            heildartexti = f"Villa við lestur: {str(e)}"
            sidur = 0
    else:
        # PDF Logic (Original)
        import concurrent.futures as _cf
        
        def _parse_pdf(data):
            parts, pages = [], 0
            with fitz.open(stream=data, filetype="pdf") as doc:
                pages = len(doc)
                for idx, pg in enumerate(doc):
                    t = pg.get_text().strip()
                    if t: parts.append(f"[Síða {idx+1}]\n{t}")
            return pages, parts

        texti_hlutar, sidur = [], 0
        if _is_vault:
            # VAULT: zero disk write
            with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_parse_pdf, efni)
                try:
                    sidur, texti_hlutar = fut.result(timeout=90)
                except _cf.TimeoutError:
                    raise HTTPException(status_code=504, detail="Vinnsla tók of langan tíma.")
        else:
            # GENERAL: disk write + cleanup
            skra_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            skra_slod = SECURE_DOCS_DIR / f"doc_{skra_id}.pdf"
            try:
                skra_slod.write_bytes(efni)
                with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(_parse_pdf, efni)
                    try:
                        sidur, texti_hlutar = fut.result(timeout=90)
                    except _cf.TimeoutError:
                        raise HTTPException(status_code=504, detail="Vinnsla tók of langan tíma.")
            finally:
                if skra_slod.exists(): skra_slod.unlink()
        
        heildartexti = "\n\n".join(texti_hlutar)

    if not heildartexti.strip():
        return JSONResponse(content={
            "success": False,
            "error": "Ekki tókst að lesa texta úr PDF (gæti verið skannað mynd).",
            "sidur": sidur,
        })

    # — 6. Skila grunnupplýsingum (LLM greining kemur í Lag 2) —
    # Sprint 62 Patch A: Only run fitz (PDF parser) for PDF files.
    # xlsx/docx already parsed above via openpyxl/python-docx.
    _parts = []
    if _filetype == 'pdf':
        import fitz as _fitz_inner
        with _fitz_inner.open(stream=efni, filetype="pdf") as _doc:
            sidur = len(_doc)
            for _pg in _doc:
                _t = _pg.get_text().strip()
                if _t: _parts.append(_t)
    # Default result fallback for all filetypes
    result = {"response": heildartexti if "heildartexti" in dir() else "", "citations": [], "found": bool(heildartexti.strip()) if "heildartexti" in dir() else False}

    # Build result dict for PDF fallback
    if _filetype == 'pdf':
        result = {"response": " ".join(_parts[:3000]), "citations": [], "found": bool(_parts)}
    import os as _os
    _tier = request.headers.get("X-Alvitur-Tier", "general").lower()
    _summary = None
    _pipeline_source_doc = "unknown"
    _domain_doc = "general"
    if _tier in ("general", "vault"):
        try:
            # 🟢 Sprint 62 Patch F: no-key → sovereign Leið B fyrir file-upload
            _key_preflight = _os.environ.get("OPENROUTER_API_KEY", "")
            if not _key_preflight and _tier != "vault":
                logger.warning("[ALVITUR] Sprint62F file-upload NO-KEY → sovereign Leið B")
                _msg_fallback = f"SPURNING: {(query or '').strip() or 'Greindu þetta skjal.'}\n\nSKJAL:\n{heildartexti[:30000]}"
                try:
                    async with _VAULT_SEMAPHORE_WS:
                        _summary, _model_used, _usage = await _call_leid_b(_msg_fallback)
                except Exception as _fe:
                    logger.error(f"[ALVITUR] Sprint62F exc: {type(_fe).__name__}: {_fe}")
                    _summary = None
                if _summary is not None:
                    _pipeline_source_doc = f"sovereign_nokey_file_{_model_used}"
                    logger.info(f"[ALVITUR] Sprint62F sovereign OK model={_model_used}")
                    # 🟢 Sprint 62 Patch I: EARLY RETURN — ekki keyra leið A aftur!
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    logger.info(f"[ALVITUR] Sprint62I early-return (skip leid_a) in={_in_tok} out={_out_tok}")
                    return JSONResponse(status_code=200, content={
                        "success": True,
                        "filename": _filename if "_filename" in dir() else "",
                        "sidur": sidur if "sidur" in dir() else 1,
                        "zero_data": True,
                        "tier": _tier,
                        "query": (query or "").strip(),
                        "response": _summary,
                        "domain": "general",
                        "citations": [],
                        "found": True,
                        "status": "ready_for_analysis",
                        "quota_warning": None,
                        "pipeline_source": _pipeline_source_doc,
                    })
            _key = _os.environ.get("OPENROUTER_API_KEY", "")
            _context_limit = 60000 if _tier == "vault" else 30000
            _full = heildartexti[:_context_limit]
            if _full:
                if query and query.strip():
                    truncation_note = " [Skjal styttur vegna stærðar]" if len(heildartexti) > _context_limit else ""
                    _msg = f"""SPURNING: {query.strip()}

REGLUR:
1. Svaraðu BEINT spurningunni hér að ofan á íslensku.
2. Notaðu skjalið AÐEINS sem heimild til að styðja við svarið.
3. EKKI endurskrifa skjalið, EKKI draga það saman nema beðið sé um það sérstaklega.
4. Ef upplýsingar vantar í skjalinu, segðu það hreint út.

SKJAL{truncation_note}:
{_full}"""
                else:
                    _msg = f"""Greindu þetta skjal stuttlega á íslensku (max 3 setningar).
Áhersla á meginþætti og ályktanir.

SKJAL:
{_full[:3000]}"""
                # Sprint 61: Leid A/B sovereign separation
                if _tier == "vault":
                    from interfaces.config import VAULT_MAX_INPUT_TOKENS as _vmax
                    if _estimate_tokens(_msg) > _vmax:
                        return JSONResponse(status_code=413, content={
                            "error_code": "vault_input_too_large",
                            "detail": f"Skjal er of stórt fyrir Vault tier (max {_vmax} tokens). Skiptu í smærri hluta eða notaðu Almenna greiningu."})
                    logger.info(f"[ALVITUR] Sprint61 analyze_doc tier=vault calling leid_b")
                    async with _VAULT_SEMAPHORE_WS:
                        _summary, _model_used, _usage = await _call_leid_b(_msg)
                    if _summary is None:
                        return JSONResponse(status_code=503, content={
                            "error_code": "vault_local_unavailable",
                            "detail": "Trúnaðarþjónusta tímabundið ekki tiltæk. Local AI module er að ræsast — reyndu aftur eftir 1 mínútu."})
                    _pipeline_source_doc = f"local_vllm_{_model_used}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    logger.info(f"[ALVITUR] leid_b analyze_doc in={_in_tok} out={_out_tok}")
                    _domain_doc = "vault"
                else:
                    from datetime import datetime as _dt, timezone as _tz
                    from interfaces.specialist_prompts import classify as _classify, get_specialist_prompt as _get_prompt
                    _classify_text = (query.strip() if query and query.strip() else heildartexti[:500])
                    try:
                        _domain_doc = await _classify(_classify_text or "general")
                    except Exception:
                        _domain_doc = "general"
                    _domain_doc = _domain_doc or "general"
                    _now_str = _dt.now(_tz.utc).strftime("%Y-%m-%d %H:%M UTC")
                    _honesty_doc = (
                        "\n\nMikilvægt: Ef þú finnur ekki nógu nákvæmar upplýsingar í skjalinu "
                        "til að svara spurningunni, segjum notandanum það beint og bjóðum upp á "
                        "framhaldsspurningu. Búðu ALDREI til upplýsingar sem eru ekki í skjalinu."
                    )
                    _system_prompt = _get_prompt(_domain_doc, _now_str) + _honesty_doc
                    logger.info(f"[ALVITUR] Sprint61 analyze_doc tier=general calling leid_a domain={_domain_doc}")
                    _summary, _model_used, _usage = await _call_leid_a(_system_prompt, _msg)
                    if _summary is None:
                        # Sprint 62 Patch C: Leið A klikkaði → sovereign fallback á Leið B
                        logger.warning("[ALVITUR] Sprint62C analyze_doc: Leið A None, reyni fallback á Leið B")
                        try:
                            async with _VAULT_SEMAPHORE_WS:
                                _summary, _model_used, _usage = await _call_leid_b(_msg)
                        except Exception as _fe:
                            logger.error(f"[ALVITUR] Sprint62C analyze_doc fallback exc: {type(_fe).__name__}: {_fe}")
                            _summary = None
                        if _summary is None:
                            return JSONResponse(status_code=503, content={
                                "error_code": "both_pipelines_unavailable",
                                "detail": "Þjónusta tímabundið ekki aðgengileg. Reyndu eftir augnablik."})
                        _pipeline_source_doc = f"fallback_local_{_model_used}"
                        logger.info(f"[ALVITUR] Sprint62C analyze_doc fallback OK: model={_model_used}")
                    else:
                        _pipeline_source_doc = f"openrouter_{_model_used.split('/')[-1]}"
                    _in_tok = _usage.get("prompt_tokens", 0); _out_tok = _usage.get("completion_tokens", 0)
                    _cost = (_in_tok * 0.15 + _out_tok * 0.60) / 1_000_000 if "gpt-4o-mini" in _model_used else (_in_tok * 3.00 + _out_tok * 15.00) / 1_000_000 if "claude-sonnet" in _model_used else 0.0
                    logger.info("[ALVITUR] token_obs pipeline=analyze_doc model=%s tier=%s in=%d out=%d cost=%.6f", _model_used, _tier, _in_tok, _out_tok, _cost)
                    # Polish only for Leid A (never vault — sovereignty)
                    try:
                        # from interfaces.chat_routes import _polish as _polish_fn
                        _summary = await _polish_fn(_summary, _key)
                    except Exception as _pe:
                        logger.warning(f"[ALVITUR] polish failed (non-fatal): {_pe}")
        except Exception as _e:
            logger.error(f"[ALVITUR] analyze_doc pipeline exc: {type(_e).__name__}: {_e}")
            _summary = None
            _domain_doc = "general"
            _pipeline_source_doc = "error"
    response = {
        "success": True,
        "filename": file.filename,
        "sidur": sidur,
        "zero_data": True,
        "tier": _tier,
        "query": query or "",
        "response": _summary or result.get("response", ""),
        "domain": _domain_doc if "_domain_doc" in dir() else "general",
        "citations": result.get("citations", []),
        "found": result.get("found", False),
        "status": "ready_for_analysis",
        "quota_warning": _quota_warning,
        "pipeline_source": _pipeline_source_doc if "_pipeline_source_doc" in dir() else "unknown",
    }
    return JSONResponse(content=response)


@app.post("/api/chat")
async def chat_endpoint(request: Request):
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

    from interfaces.chat_routes import handle_chat
    return await handle_chat(request, query, tier)


# ── Sprint 28: K6 — /oryggi trust page ───────────────────────────────────────
@app.get("/oryggi", response_class=HTMLResponse)
async def oryggi_page():
    """Sprint 29 T1 — Trust Center"""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="is">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Öryggi | Alvitur</title>
  <meta name="description" content="Hvernig Alvitur meðhöndlar gögn, trúnað og skjalasendingar.">
  <meta property="og:title" content="Öryggi | Alvitur">
  <meta property="og:description" content="Ekkert vistast í trúnaðarham. Sjálfvirk gagnaeyðing. GDPR-samræmt.">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600&display=swap">
  <style>
/* Alvitur.is Design System */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-font-smoothing: antialiased; scroll-behavior: smooth; scroll-padding-top: 5rem; }
:root {
  --font-display: 'General Sans', 'Helvetica Neue', sans-serif;
  --font-body: 'Inter', 'Helvetica Neue', sans-serif;
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.75vw, 1.375rem);
  --text-hero: clamp(2.5rem, 1rem + 4vw, 4rem);
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
  --space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem; --space-10: 2.5rem;
  --space-12: 3rem; --space-16: 4rem; --space-20: 5rem;
  --color-bg: #F5F4F0;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-text-muted: #6B6B6B;
  --color-text-faint: #A3A3A3;
  --color-accent: #0A6B6E;
  --color-accent-hover: #085456;
  --color-accent-light: rgba(10, 107, 110, 0.08);
  --color-accent-border: rgba(10, 107, 110, 0.25);
  --color-border: #E2E0DA;
  --color-border-light: #ECEAE5;
  --color-error: #B5364B;
  --color-success: #2D7A3E;
  --radius-sm: 0.375rem; --radius-md: 0.625rem; --radius-lg: 0.875rem; --radius-xl: 1rem;
  --shadow-card: 0 1px 3px rgba(26,26,26,0.04), 0 4px 16px rgba(26,26,26,0.06);
  --shadow-card-hover: 0 2px 8px rgba(26,26,26,0.06), 0 8px 24px rgba(26,26,26,0.08);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --transition-fast: 150ms var(--ease-out);
  --transition-normal: 250ms var(--ease-out);
  --content-max: 680px;
  --content-wide: 960px;
  --nav-height: 3.75rem;
}
body { min-height: 100dvh; line-height: 1.6; font-family: var(--font-body); font-size: var(--text-base); color: var(--color-text); background-color: var(--color-bg); }
h1,h2,h3,h4,h5,h6 { text-wrap: balance; line-height: 1.15; }
p,li { text-wrap: pretty; max-width: 72ch; }
button { cursor: pointer; background: none; border: none; font: inherit; color: inherit; }
/* NAV */
.nav { position: fixed; top: 0; left: 0; right: 0; z-index: 50; height: var(--nav-height); background: rgba(245,244,240,0.92); backdrop-filter: blur(12px); border-bottom: 1px solid var(--color-border-light); }
.nav__inner { max-width: var(--content-wide); margin: 0 auto; padding: 0 var(--space-6); height: 100%; display: flex; align-items: center; justify-content: space-between; }
.nav__logo { display: flex; align-items: center; gap: var(--space-2); text-decoration: none; color: var(--color-text); }
.nav__logo-text { font-family: var(--font-display); font-weight: 600; font-size: 1.25rem; letter-spacing: -0.02em; }
.nav__links { display: flex; align-items: center; gap: var(--space-6); }
.nav__link { font-size: var(--text-sm); font-weight: 500; color: var(--color-text-muted); text-decoration: none; }
.nav__link:hover { color: var(--color-accent); }
/* ORYGGI PAGE */
.oryggi-main { max-width: var(--content-max); margin: 0 auto; padding: calc(var(--nav-height) + var(--space-12)) var(--space-6) var(--space-16); }
.oryggi-main h1 { font-family: var(--font-display); font-size: clamp(1.75rem, 3vw, 2.25rem); font-weight: 600; letter-spacing: -0.02em; margin-bottom: var(--space-8); }
.oryggi-section { margin-bottom: var(--space-10); }
.oryggi-section h2 { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-4); }
.oryggi-section p { font-size: var(--text-base); color: var(--color-text-muted); line-height: 1.7; margin-bottom: var(--space-4); }
.oryggi-cta { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-6); background: var(--color-accent); color: #FFFFFF; font-size: var(--text-sm); font-weight: 600; text-decoration: none; border-radius: var(--radius-md); margin-top: var(--space-4); }
.oryggi-cta:hover { background: var(--color-accent-hover); }
.oryggi-trust { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-xs); color: var(--color-text-faint); margin-top: var(--space-3); }
/* FOOTER */
.footer { padding: var(--space-8) var(--space-6); border-top: 1px solid var(--color-border-light); }
.footer__inner { max-width: var(--content-wide); margin: 0 auto; text-align: center; }
.footer__copy { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__copy a, .footer__links a { color: var(--color-text-muted); text-decoration: none; }
.footer__copy a:hover, .footer__links a:hover { color: var(--color-accent); }
.footer__links { font-size: var(--text-xs); color: var(--color-text-muted); margin-bottom: var(--space-2); }
.footer__links span { margin: 0 var(--space-2); }
.footer__eea { font-size: var(--text-xs); color: var(--color-text-faint); }
@media (max-width: 640px) {
  :root { --nav-height: 3.25rem; }
  .oryggi-main { padding-top: calc(var(--nav-height) + var(--space-8)); }
}
  </style>
</head>
<body>
  <nav class="nav" role="navigation" aria-label="Aðalvalmynd">
    <div class="nav__inner">
      <a href="/" class="nav__logo" aria-label="Alvitur forsíða">
        <svg class="nav__logo-mark" viewBox="0 0 28 28" fill="none" aria-hidden="true" width="28" height="28">
          <rect width="28" height="28" rx="6" fill="currentColor" opacity="0.1"/>
          <path d="M7 21L14 7L21 21M10.5 16h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span class="nav__logo-text">Alvitur</span>
      </a>
      <div class="nav__links">
        <a href="/oryggi" class="nav__link">Öryggi</a>
        <a href="/" class="nav__link">&larr; Til baka</a>
      </div>
    </div>
  </nav>

  <main class="oryggi-main">
    <h1>Öryggi og gagnaforræði</h1>

    <section class="oryggi-section">
      <h2>Engin þjálfun á þínum gögnum</h2>
      <p>Hjá Alvitri teljum við að stofnanir og fyrirtæki eigi ekki að þurfa að velja á milli þess að nýta kraft öflugustu gervigreindar heims og þess að vernda viðkvæm gögn. Við höfum smíðað íslenskt vinnsluumhverfi og arkitektúr sem tryggir fullt gagnaforræði í hverju skrefi.</p>
      <p>Við nýtum eingöngu lokuð fyrirtækjaskil (Enterprise APIs) við stærstu mállíkön heims, þar sem gilda ströng skilyrði um gagnavernd. Við ábyrgjumst lagalega og tæknilega að hvorki skjöl né fyrirspurnir sem fara í gegnum Alvitur verði nokkurn tímann nýtt til að þjálfa, fínstilla eða bæta gervigreindarlíkön birgja okkar. Hugverkið þitt er varið.</p>
    </section>

    <section class="oryggi-section">
      <h2>Sjálfvirk gagnaeyðing í trúnaðarham</h2>
      <p>Fyrir viðkvæmustu upplýsingarnar krefst kerfið þess að notandi velji Trúnaðarvinnslu (Leið B). Undir þessu vinnslulagi eru skjöl lesin beint inn í vinnsluminni (RAM) á netþjónum okkar &mdash; þau snerta aldrei varanlegan harðan disk.</p>
      <p>Að greiningu lokinni er minnið hreinsað og gögnin eyðast sjálfkrafa. Engin varanleg afrit verða til. Það er ekki hægt að ná í gögn sem eru ekki lengur til.</p>
    </section>

    <section class="oryggi-section">
      <h2>Lögsaga og evrópskir innviðir</h2>
      <p>Allur vélbúnaður sem knýr gagnagátt Alviturs er hýstur í vottuðum gagnaverum innan Evrópska efnahagssvæðisins (EES). Kerfið lútur persónuverndarlögum (GDPR) að fullu.</p>
      <p>Með innbyggðri gagnaflokkun styður Alvitur við kröfur ISO 42001 og komandi löggjöf Evrópusambandsins (EU AI Act) um ábyrga og rekjanlega notkun gervigreindar.</p>
    </section>

    <section class="oryggi-section">
      <h2>Sannanlegur rekjanleiki</h2>
      <p>Til að styðja við örugga skjalavörslu og innri endurskoðun heldur kerfið utan um dulkóðaða atvikaskrá (Audit Trail). Við skráum að vinnsla á ákveðnu öryggisstigi fór fram, ásamt metadata og tímasetningu, en innihald gagnanna eða skjalsins sjálfs er aldrei varðveitt á Trúnaðarleiðinni.</p>
    </section>

    <div style="text-align: center; padding: var(--space-8) 0;">
      <a href="/" class="oryggi-cta">
        Hefja örugga greiningu
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M3.75 9h10.5M9.75 4.5L14.25 9l-4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </a>
      <div class="oryggi-trust">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 1L2 3.25v4C2 10.2 4.2 12.75 7 13.5c2.8-.75 5-3.3 5-6.25v-4L7 1z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/></svg>
        Styður við kröfur ISO 42001 og GDPR
      </div>
    </div>
  </main>

  <footer class="footer" role="contentinfo">
    <div class="footer__inner">
      <p class="footer__copy">&copy; 2026 Orkuskipti ehf &middot; <a href="mailto:info@alvitur.is">info@alvitur.is</a></p>
      <p class="footer__links"><a href="/personuvernd">Persónuverndarstefna</a><span>&middot;</span><a href="/skilmalar">Skilmálar</a></p>
      <p class="footer__eea">Gögn unnin innan EES</p>
    </div>
  </footer>
</body>
</html>""")
# ── Sprint 43b: /askrift pricing page ──────────────────────────────────────────
@app.get("/askrift", response_class=HTMLResponse)
async def askrift_page():
    """Sprint 43b — Pricing / subscription page."""
    try:
        from sprint43.pricing_page import render_pricing_page
        return HTMLResponse(content=render_pricing_page())
    except ImportError:
        return HTMLResponse(content="""<!DOCTYPE html>
<html lang="is"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Áskrift — Alvitur</title>
<style>body{font-family:system-ui,sans-serif;background:#0F1117;color:#E2E8F0;display:flex;justify-content:center;padding:3rem}
.c{max-width:600px;text-align:center}h1{margin-bottom:1rem}p{color:#94A3B8;margin-bottom:.5rem}
a{color:#6366F1}</style></head><body><div class="c">
<h1>Áskrift — Alvitur</h1>
<p>Brons: 990 kr/mán — 100 fyrirspurnir</p>
<p>Silfur: 4.990 kr/mán — 1.000 fyrirspurnir</p>
<p>Gull: 14.990 kr/mán — 5.000 fyrirspurnir</p>
<p style="margin-top:1.5rem"><a href="mailto:info@alvitur.is">Hafðu samband</a></p>
</div></body></html>""")


# ─────────────────────────────────────────────────────────────────────────────


@app.get("/mock-checkout/{plan}/{amount}/{user_id}", response_class=HTMLResponse)
async def checkout(plan: str, amount: int, user_id: str):
    return HTMLResponse(content="<h2 style='font-family:system-ui;color:#e5e5e5;background:#0a0a0a;padding:3rem;text-align:center'>Áskriftarlegar eru ekki opnar enn. Hafðu samband: info@alvitur.is</h2>", status_code=503)


@app.post("/api/webhook/mock_success", response_class=HTMLResponse)
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

@app.get("/alvitur-v2", response_class=HTMLResponse)
async def serve_v2():
    with open('index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/mimir-demo", response_class=HTMLResponse)
async def serve_demo():
    with open('index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


# ═══════════════════════════════════════════════════════════════════════
# Sprint 61 - Leid A/B helpers (sovereign separation)
# ═══════════════════════════════════════════════════════════════════════

async def _call_leid_a(system_prompt, user_msg, max_tokens=1500):
    """OpenRouter chain: Haiku -> Sonnet -> gpt-4o-mini. Returns (content, model, usage)."""
    from interfaces.config import MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY
    import httpx as _hx
    _key = os.environ.get("OPENROUTER_API_KEY", "")
    if not _key:
        logger.error("[ALVITUR] leid_a: OPENROUTER_API_KEY missing")
        return (None, None, None)
    if os.environ.get("OPENROUTER_ZDR_CONFIRMED", "false") != "true":
        logger.warning("[ALVITUR] leid_a: ZDR_CONFIRMED=false - refusing call")
        return (None, None, None)
    chain = [MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY]
    async with _hx.AsyncClient() as c:
        for idx, model in enumerate(chain):
            try:
                r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {_key}", "HTTP-Referer": "https://alvitur.is", "X-Title": "Alvitur"},
                    json={"model": model, "messages": [{"role":"system","content":system_prompt},{"role":"user","content":user_msg}], "max_tokens": max_tokens},
                    timeout=30.0)
                if r.status_code != 200:
                    logger.warning(f"[ALVITUR] leid_a step={idx+1}/3 model={model} status={r.status_code}")
                    continue
                d = r.json()
                logger.info(f"[ALVITUR] leid_a {'FALLBACK' if idx>0 else 'primary'} ok step={idx+1}/3 model={model}")
                return (d["choices"][0]["message"]["content"], model, d.get("usage", {}))
            except Exception as e:
                logger.warning(f"[ALVITUR] leid_a step={idx+1}/3 exc={type(e).__name__}: {e}")
    logger.error("[ALVITUR] leid_a ALL 3 models failed")
    return (None, None, None)


def _vault_system_prompt():
    return ("Þú ert Alvitur — íslensk gervigreindaraðstoð á trúnaðarstigi (Vault). "
            "Þú keyrir á íslenskri GPU. Gögn fara aldrei úr vélinni.\n\n"
            "REGLUR UM ÍSLENSKU:\n"
            "1. Svaraðu ALLTAF á réttri íslensku með fullum beygingum.\n"
            "2. Gættu að föllum (nf/þf/þgf/ef) og kynjum (kk/kvk/hk).\n"
            "3. Notaðu aldrei orð sem þú ert ekki viss um — veldu einfaldara orð.\n"
            "4. Ekki búa til orð. Ef þú veist ekki orðið — umorðaðu.\n\n"
            "DÆMI UM GÓÐA SVÖRUN:\n"
            "Spurning: Hvað er höfuðborg Íslands?\n"
            "Svar: Reykjavík er höfuðborg Íslands. Hún er stærsta borg landsins og þar búa um 130.000 manns.\n\n"
            "Spurning: Greindu þessa færslu: '01.12.2025 | Launagreiðsla | 450000'\n"
            "Svar: Þetta er innborgun launa að fjárhæð 450.000 krónur þann 1. desember 2025. Þetta flokkast sem tekjur.\n\n"
            "Svaraðu nú spurningu notandans í sama stíl.")


async def _call_leid_b(user_msg, max_tokens=8192):
    """Local sovereign vLLM. NO cloud fallback. Returns (content, model, usage) or (None,None,None)."""
    from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT
    import httpx as _hx
    try:
        async with _hx.AsyncClient() as c:
            r = await c.post(VAULT_LOCAL_URL,
                headers={"Content-Type": "application/json"},
                json={"model": VAULT_LOCAL_MODEL,
                      "messages": [{"role":"system","content":_vault_system_prompt()},{"role":"user","content":user_msg}],
                      "max_tokens": max_tokens, "temperature": 0.3, "top_p": 0.9,
                      "chat_template_kwargs": {"enable_thinking": False}},
                timeout=float(VAULT_LOCAL_TIMEOUT))
            if r.status_code != 200:
                logger.error(f"[ALVITUR] leid_b local vLLM status={r.status_code} body={r.text[:200]}")
                return (None, None, None)
            d = r.json()
            ms = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
            u = d.get("usage", {})
            logger.info(f"[ALVITUR] leid_b sovereign ok model={ms} in={u.get('prompt_tokens',0)} out={u.get('completion_tokens',0)}")
            return (d["choices"][0]["message"]["content"], ms, u)
    except Exception as e:
        logger.error(f"[ALVITUR] leid_b local vLLM exc={type(e).__name__}: {e}")
        return (None, None, None)


def _estimate_tokens(text):
    return int(len((text or "").split()) * 1.3)
