"""Security headers middleware for Alvitur.

Sprint 71 Track A.4c — extracted from interfaces/web_server.py.
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("alvitur.web")

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

