"""Exception handlers — flutt úr web_server.py (Sprint 71 A.4e)."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
