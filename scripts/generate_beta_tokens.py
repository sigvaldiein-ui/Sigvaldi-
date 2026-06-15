from pathlib import Path

def _load_jwt_key(key_type="private"):
    """Les JWT lykil úr PEM skrá ef slóð er til, annars úr env."""
    env_key = f"JWT_{key_type.upper()}_KEY"
    path_key = f"JWT_{key_type.upper()}_KEY_PATH"
    path = os.environ.get(path_key, "")
    if path and Path(path).exists():
        with open(path, 'r') as f:
            return f.read()
    return os.environ.get(env_key, "dummy-dev-key")
import jwt
import os

key = _load_jwt_key("public")

tokens = [
    {"sub": "beta-admin", "org_id": "orkuskipti-prod", "tier": "Hvelfingin", "jti": "beta-admin-001"},
    {"sub": "beta-expert", "org_id": "orkuskipti-prod", "tier": "Vitinn", "jti": "beta-expert-002"},
    {"sub": "beta-agent", "org_id": "orkuskipti-prod", "tier": "Starfsmaður", "jti": "beta-agent-003"},
]

print("=== BETA TOKENS ===")
for t in tokens:
    token = jwt.encode(t, key, algorithm="RS256")
    print(f"\n{t['sub']} ({t['tier']}):")
    print(token)
