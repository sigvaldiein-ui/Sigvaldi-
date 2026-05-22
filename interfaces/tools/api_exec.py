from interfaces.tools.base import BaseTool
from fastapi.exceptions import HTTPException
from urllib.parse import urlparse

ALLOWED_DOMAINS = {"api.skra.is", "island.is", "api.logbirting.is"}

class Api_execTool(BaseTool):
    @property
    def name(self) -> str:
        return "api_exec"
    @property
    def description(self) -> str:
        return "Whitelisted API execution"
    async def run(self, **kwargs):
        url = kwargs.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        domain = urlparse(url).netloc
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=400, detail=f"Domain '{domain}' not whitelisted")
        return {"status": "sandboxed_ok", "url": url, "domain": domain}
    def to_mcp_schema(self) -> dict:
        return {"name": "api_exec", "description": "Whitelisted API execution"}
