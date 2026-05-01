"""User model — Sprint 73 Fasi 3: Auðkenni OIDC."""
import hashlib
import os
from datetime import datetime, timezone
from pydantic import BaseModel, Field

APP_SALT = os.getenv("APP_SALT", "alvitur-fast-salt-change-in-prod")


def hash_kennitala(kennitala: str) -> str:
    """SHA-256 hash af kennitölu með föstu app-salti."""
    return hashlib.sha256(f"{kennitala}{APP_SALT}".encode()).hexdigest()


def generate_user_salt() -> str:
    """Einstakt salt per notanda — geymt í users töflu."""
    return os.urandom(16).hex()


class User(BaseModel):
    """Alvitur notandi — sannvottaður í gegnum Auðkenni."""
    id: int | None = None
    kennitala_hash: str
    salt: str
    nafn: str = ""
    email: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
