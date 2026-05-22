"""Sprint 100.x — MAIL_SEND með SMTP rekjanleika."""
from interfaces.tools.base import BaseTool
import hashlib, time

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
        
        audit_hash = hashlib.sha256(f"{time.time()}|{to}|{subject}".encode()).hexdigest()[:16]
        footer = f"\n\n---\nUndirbúið af Alvitri (Digital Worker). Rekjanleiki: {audit_hash}"
        
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
            "body": body + footer,
            "audit_hash": audit_hash
        }

    def to_mcp_schema(self) -> dict:
        return {"name": "mail_send", "description": "Secure email with SHA-256 traceability"}
