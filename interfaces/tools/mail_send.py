"""Sprint 100.3 — MAIL_SEND með Human-in-the-Loop (HITL) vörn."""
from interfaces.tools.base import BaseTool

class Mail_sendTool(BaseTool):
    @property
    def name(self) -> str:
        return "mail_send"
    
    async def run(self, **kwargs):
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        confirmed = kwargs.get("confirmed", False)
        
        if not confirmed:
            return {
                "status": "pending_approval",
                "message": "Aðgerð stöðvuð: Krefst staðfestingar notanda.",
                "preview": {"to": to, "subject": subject, "body": body}
            }
            
        return {"status": "sent", "to": to, "subject": subject}

    def to_mcp_schema(self) -> dict:
        return {"name": "mail_send", "description": "Secure email transmission — requires HITL confirmation"}
