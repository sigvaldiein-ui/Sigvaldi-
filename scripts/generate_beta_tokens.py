import jwt
import os

key = os.environ.get("JWT_PUBLIC_KEY", "dummy-dev-key")

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
