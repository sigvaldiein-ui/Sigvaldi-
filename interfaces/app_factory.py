from dotenv import load_dotenv
load_dotenv("/workspace/.env", override=True)

"""App factory — flutt úr web_server.py (Sprint 71 A.4e)."""
import logging
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
from interfaces.middleware.security import SecurityHeadersMiddleware
from interfaces.middleware.auth import AuthMiddleware
from interfaces.middleware.errors import validation_exception_handler
from interfaces.routes.health import router as health_router
from interfaces.routes.tools import router as tools_router
from interfaces.routes.hvelfing import router as hvelfing_router
from interfaces.routes.checkout import router as checkout_router
from interfaces.routes.pages import router as pages_router
from interfaces.routes.auth import callback_router
from interfaces.routes.analyze import router as analyze_router
from interfaces.routes.chat import router as chat_router
from interfaces.routes.auth import router as auth_router

logger = logging.getLogger("alvitur.web")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Alvitur Enterprise AI",
        docs_url=None,
        redoc_url=None,
    )

    app.include_router(pages_router)
    app.include_router(health_router)
    app.include_router(tools_router)
    app.include_router(checkout_router)
    app.include_router(analyze_router)
    app.include_router(callback_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(hvelfing_router)

    app.exception_handler(RequestValidationError)(validation_exception_handler)

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))
    app.add_middleware(AuthMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    _static_dir = "/workspace/mimir_net/interfaces/static"
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

    return app
