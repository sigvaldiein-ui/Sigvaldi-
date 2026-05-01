from interfaces.middleware.auth import require_auth
"""MCP tools registry endpoints for Alvitur.

Sprint 71 Track A.4b — extracted from interfaces/web_server.py.

Endpoints:
- GET  /api/tools            — list available MCP tools
- POST /api/tools/{name}     — invoke an MCP tool by name
"""
import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

logger = logging.getLogger("alvitur.web")
router = APIRouter()


# --- tools_list ---
@router.get("/api/tools")
async def tools_list(request: Request, user = Depends(require_auth)):
    """
    Sprint 59: Skilar lista af öllum tiltækum tools.
    MCP-samhæft — notað af MCP clients og /api/tools wiring.
    """
    from interfaces.mcp_server import mcp_list_tools
    tools = await mcp_list_tools()
    return JSONResponse(content={"success": True, "tools": tools, "count": len(tools)})



# --- tools_call ---
@router.post("/api/tools/{tool_name}")
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

