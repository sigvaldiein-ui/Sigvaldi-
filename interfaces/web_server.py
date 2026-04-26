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
from interfaces.routes.health import router as health_router
from interfaces.routes.tools import router as tools_router
from interfaces.routes.checkout import router as checkout_router
from interfaces.static_content.html_pages import (
    SHARED_HEAD, SHARED_STYLES,
    SVG_LOGO, SVG_LOGO_CHAT, CHECK_SVG, ACCENT_CHECK, NAV_SCRIPT, HTML_PAGE,
)
from interfaces.pipeline import _call_leid_a, _call_leid_b, _vault_system_prompt
from interfaces.routes.pages import router as pages_router
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
app.include_router(pages_router)  # A.4a pages
app.include_router(health_router)
app.include_router(tools_router)
app.include_router(checkout_router)

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


# ─── SVG Logo ─────────────────────────────────────────────────────────────────

# ─── Check SVG ────────────────────────────────────────────────────────────────

# ─── Nav Script ───────────────────────────────────────────────────────────────

# ─── Sprint 44: Frontend Redesign — Light theme ──────────────────────────────



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
                # s68-hotfix Part 3: text-only + tone-guide + thinking-suppress
                _honesty = (
                    "\n\nMikilvægt: Notandi hefur ekki hengt við skjal — þetta er almenn "
                    "spurning. Svaraðu út frá almennri þekkingu þinni á íslensku. "
                    "Ef þú veist ekki svarið með vissu, segðu það heiðarlega og bjóddu "
                    "framhaldsspurningu. Ekki búa til staðreyndir. "
                    "MIKILVÆGT UM FRAMSETNINGU: Ekki sýna hugsanaferli þitt — engar "
                    "<thinking>-tög, engin ‚bíð, ég þarf að“ setningar, engin internal-monologue. "
                    "Sendu aðeins hreint, prófessjónal svar beint. Engar emoji, "
                    "engin upphrópunarmerki, formlegt B2B-mál."
                )
                _system_prompt = _get_prompt(_domain_txt, _now_str) + _honesty
                # Sprint 70 Track D — RAG+ hook (text-only path)
                try:
                    from core.rag_orchestrator import retrieve_legal_context, build_rag_injection
                    _rag_txt = retrieve_legal_context(
                        query=(query or "").strip(),
                        intent_domain=_domain_txt,
                        tier=_tier,
                        tenant_id="system",
                    )
                    if _rag_txt.refusal:
                        from fastapi.responses import JSONResponse as _JR
                        return _JR(content={"success":True,"response":_rag_txt.refusal,
                            "pipeline_source":"rag_refusal_vault","domain":_domain_txt,
                            "zero_data":True,"found":True,"status":"ready_for_analysis",
                            "citations":[],"quota_warning":None,"tier":_tier})
                    if _rag_txt.used_retrieval:
                        _system_prompt = _system_prompt + build_rag_injection(_rag_txt.chunks)
                        _pipeline_source_txt = "rag_grounded_" + _tier
                    elif _rag_txt.fallback_to_gemini:
                        _system_prompt = _system_prompt + "[ATH: Engin lagatilvitnun fannst. Svaraðu varlega.]"
                        _pipeline_source_txt = "rag_fallback_general"
                except Exception as _rag_e2:
                    logger.warning("[RAG] text-only villa: %s", _rag_e2)
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
            "rag_metadata": _rag_txt.__dict__ if hasattr(_rag_txt,"used_retrieval") else {},
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
    _rag_doc_meta = {"used_retrieval": False, "chunks_count": 0, "top_score": 0.0, "low_confidence": False, "source_laws": []}
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
                    # s68-hotfix: conditional honesty — document vs text-only mode
                    _has_document = bool(file and getattr(file, "filename", "") and file.filename.strip())
                    if _has_document:
                        _honesty_doc = (
                            "\n\nMikilvægt: Ef þú finnur ekki nógu nákvæmar upplýsingar í skjalinu "
                            "til að svara spurningunni, segjum notandanum það beint og bjóðum upp á "
                            "framhaldsspurningu. Búðu ALDREI til upplýsingar sem eru ekki í skjalinu."
                        )
                    else:
                        # s68-hotfix Part 3: tone-guide + thinking-suppress
                        _honesty_doc = (
                            "\n\nMikilvægt: Notandi hefur ekki hengt við skjal — þetta er almenn "
                            "spurning. Svaraðu út frá almennri þekkingu þinni á íslensku. "
                            "Ef þú veist ekki svarið með vissu, segðu það heiðarlega og bjóddu "
                            "framhaldsspurningu. Ekki búa til staðreyndir. "
                            "MIKILVÆGT UM FRAMSETNINGU: Ekki sýna hugsanaferli þitt — engar "
                            "<thinking>-tög, engin ‚bíð, ég þarf að“ setningar, engin internal-monologue. "
                            "Sendu aðeins hreint, prófessjónal svar beint. Engar emoji, "
                            "engin upphrópunarmerki, formlegt B2B-mál."
                        )
                    _system_prompt = _get_prompt(_domain_doc, _now_str) + _honesty_doc

                    # Sprint 70 Track D — RAG+ hook
                    print("DEBUG: RAG hook starting", flush=True)
                    try:
                        from core.rag_orchestrator import retrieve_legal_context, build_rag_injection
                        _rag = retrieve_legal_context(
                            query=((query or "").strip() or _msg or ""),
                            intent_domain=_domain_doc,
                            tier="general",
                            tenant_id="system",
                        )
                        if _rag.refusal:
                            return JSONResponse(content={
                                "success": True, "response": _rag.refusal,
                                "pipeline_source": "rag_refusal_vault",
                                "domain": _domain_doc, "zero_data": True,
                                "found": True, "status": "ready_for_analysis",
                                "citations": [], "quota_warning": None,
                            })
                        if _rag.used_retrieval:
                            _rag_injection = build_rag_injection(_rag.chunks)
                            _system_prompt = _system_prompt + _rag_injection
                            _pipeline_source_doc = f"rag_grounded_general"
                            _rag_doc_meta = {"used_retrieval": True, "chunks_count": len(_rag.chunks), "top_score": round(_rag.top_score,3), "low_confidence": _rag.top_score<0.65, "source_laws": []}
                            logger.info("[RAG] injected %d chunks into analyze_doc prompt", len(_rag.chunks))
                        elif _rag.fallback_to_gemini:
                            _system_prompt = _system_prompt + "[ATH: Engin lagatilvitnun fannst i corpus Alvitur. Svaraðu varlega.]"
                            _pipeline_source_doc = "rag_fallback_general"
                            _pipeline_source_doc = "rag_fallback_general"
                    except Exception as _rag_e:
                        logger.warning("[RAG] orchestrator villa (graceful degradation): %s", _rag_e)

                    _rag_doc_meta = {"used_retrieval": _rag.used_retrieval, "chunks_count": len(_rag.chunks), "top_score": round(_rag.top_score, 3), "low_confidence": _rag.top_score < 0.65, "source_laws": []} if "_rag" in dir() else {}
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
        "rag_metadata": _rag_doc_meta,
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
@app.get("/mock-checkout/{plan}/{amount}/{user_id}", response_class=HTMLResponse)
async def checkout(plan: str, amount: int, user_id: str):
    return HTMLResponse(content="<h2 style='font-family:system-ui;color:#e5e5e5;background:#0a0a0a;padding:3rem;text-align:center'>Áskriftarlegar eru ekki opnar enn. Hafðu samband: info@alvitur.is</h2>", status_code=503)


def _estimate_tokens(text):
    return int(len((text or "").split()) * 1.3)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "interfaces.web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
