#!/usr/bin/env python3
import jwt, time, uuid, sys

def issue(sub: str, org_id: str, tier: str = "Vitinn", days: int = 7):
    key = open('/workspace/Sigvaldi-/jwt_private.pem').read()
    now = int(time.time())
    claims = {
        "iss": "auth.alvitur.is",
        "sub": sub,
        "org_id": org_id,
        "tier": tier,
        "iat": now,
        "nbf": now,
        "exp": now + days*24*3600,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(claims, key, algorithm='RS256')

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: issue_beta_token.py <sub> <org_id> <Vitinn|Hvelfingin|Starfsmadur> [days]")
        sys.exit(1)
    print(issue(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 7))
