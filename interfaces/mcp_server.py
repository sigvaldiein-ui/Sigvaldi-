# interfaces/mcp_server.py
"""
Sprint 58 — MCP Server fyrir Alvitur tools.

Þetta module útfærir MCP-samhæft viðmót fyrir Tools package.
Sérhvert tool er skráð með name, description og callable run().

MCP integration:
  - list_tools(): skilar öllum tiltækum tools
  - call_tool(name, arguments): kallar á tool og skilar niðurstöðu

Þetta er innra MCP lag — web_server.py /api/tools endpointar nota þetta.
"""
import logging
from typing import Any
from interfaces.tools import REGISTRY, list_tools, get_tool

logger = logging.getLogger("alvitur.web")


async def mcp_list_tools() -> list[dict]:
    """
    Skilar MCP-samhæfum lista af öllum skráðum tools.
    Notað í /api/tools GET endpoint.
    """
    tools = list_tools()
    logger.info("[ALVITUR] mcp_list_tools count=%d", len(tools))
    return tools


async def mcp_call_tool(name: str, arguments: dict[str, Any]) -> dict:
    """
    Kallar á tool með gefnum arguments.
    Notað í /api/tools/{name} POST endpoint.

    Skilar:
      {"success": True, "result": ...}  — ef OK
      {"success": False, "error": "..."}  — ef villa eða tool ekki til
    """
    tool = get_tool(name)
    if tool is None:
        logger.warning("[ALVITUR] mcp_call_tool: tool '%s' ekki til", name)
        return {
            "success": False,
            "error": f"Tool '{name}' ekki til. Tiltæk tools: {list(REGISTRY.keys())}",
        }

    try:
        result = await tool.run(**arguments)
        logger.info("[ALVITUR] mcp_call_tool tool=%s ok", name)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("[ALVITUR] mcp_call_tool tool=%s villa: %s", name, e)
        return {"success": False, "error": str(e)}
