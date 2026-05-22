from interfaces.tools.base import BaseTool

class Pdf_genTool(BaseTool):
    @property
    def name(self) -> str:
        return "pdf_gen"
    @property
    def description(self) -> str:
        return "Generate PDF documents"
    async def run(self, **kwargs):
        return {"status": "ok"}
    def to_mcp_schema(self) -> dict:
        return {"name": "pdf_gen", "description": "PDF Generator"}
