"""Sprint 104 — Secure Audit Logger með SHA-256 keðju."""
import hashlib
import time

class SecureAuditLogger:
    def __init__(self):
        self.last_hash = "0" * 64
    
    def log_action(self, jti: str, user_sub: str, tool_name: str, action: str) -> str:
        timestamp = str(time.time())
        payload = f"{self.last_hash}|{timestamp}|{jti}|{user_sub}|{tool_name}|{action}"
        new_hash = hashlib.sha256(payload.encode()).hexdigest()
        self.last_hash = new_hash
        return new_hash
