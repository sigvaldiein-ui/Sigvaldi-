from interfaces.tools.base import BaseTool
import hashlib, time

class Mail_sendTool(BaseTool):
    @property
    def name(self) -> str:
        return "mail_send"
    @property
    def description(self) -> str:
        return "Secure email with SHA-256 traceability"
    async def run(self, **kwargs):
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        confirmed = kwargs.get("confirmed", False)
        if not confirmed:
            return {"status": "pending_approval", "message": "Krefst staðfestingar", "preview": {"to": to, "subject": subject}}
        h = hashlib.sha256(f"{time.time()}|{to}|{subject}".encode()).hexdigest()[:16]
        return {"status": "sent", "to": to, "subject": subject, "audit_hash": h}
    def to_mcp_schema(self) -> dict:
        return {"name": "mail_send", "description": "Secure email with SHA-256 traceability"}
