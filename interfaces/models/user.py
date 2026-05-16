"""User model fyrir OIDC Auðkenni."""
import hashlib, os

def hash_kennitala(kennitala: str) -> str:
    """Hasar kennitölu með salt fyrir geymslu."""
    salt = os.environ.get("KT_SALT", "dev-salt")
    return hashlib.sha256(f"{kennitala}{salt}".encode()).hexdigest()
