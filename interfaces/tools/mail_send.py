from interfaces.tools.base import BaseTool
import hashlib, time, os, smtplib, asyncio
from email.mime.text import MIMEText

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
        footer = f"\n\n---\nAlvitur Digital Worker | Rekjanleiki: {h}"
        
        def _send_sync():
            msg = MIMEText(body + footer)
            msg["Subject"] = subject
            msg["From"] = os.environ.get("SMTP_USER", "alvitur@alvitur.is")
            msg["To"] = to
            with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", "587"))) as s:
                s.starttls()
                s.login(os.environ.get("SMTP_USER", ""), os.environ.get("SMTP_PASSWORD", ""))
                s.send_message(msg)
        
        try:
            await asyncio.to_thread(_send_sync)
            return {"status": "sent", "to": to, "subject": subject, "audit_hash": h}
        except Exception as e:
            return {"status": "error", "message": f"SMTP failed: {str(e)}", "audit_hash": h}

    def to_mcp_schema(self) -> dict:
        return {"name": "mail_send", "description": "Secure email via SMTP"}
