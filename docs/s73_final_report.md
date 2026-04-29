# Sprint 73 — Final Report (Auth + OIDC)

**Branch:** sprint73-auth
**Dates:** 28-29. apríl 2026
**Status:** COMPLETE

## Scoreboard

| Fasi | Verk | Staða |
|---|---|---|
| 0 | State verification | OK |
| 1 | Pandas bal.iloc fix | OK |
| 2 | UI Vitinn/Hvelfingin | DONE pre-sprint |
| 3 | OIDC Auðkenni integration | OK |

## Files

- interfaces/models/user.py (28 lines)
- interfaces/middleware/auth.py (66 lines)
- interfaces/routes/auth.py (150 lines)
- interfaces/app_factory.py (47 lines, +AuthMiddleware)
- core/db_manager.py (178 lines, +users table)
- excel_preprocessor.py (Pandas hotfix)

Total: ~470 new lines.

## Security (Hvelfingarregla M1)

- httpOnly cookie (XSS-resistant)
- state parameter (CSRF protection, 10 min TTL)
- JWT exp claim (15 min TTL)
- algorithms=["HS256"] whitelist (algorithm confusion protection)
- Required claims: exp, iat, sub, jti
- APP_SALT + per-user salt double-hash on kennitala
- Kennitala never plaintext on disk

## Lessons Logged

- #34: httpOnly cookie + state + exp + jti = 2026 SOTA for JWT auth
- #35: APP_SALT + per-user salt = sovereign-friendly kennitala storage

## Turtle Directive v4 — New Rule

Max 150-200 lines per file. If exceeded, Opus halts and we split.
db_manager.py (178) and routes/auth.py (150) are at threshold — watch in S74.

## Auðkenni Integration Status

- Test client_id: orkuskiptiOidcTest
- Base URL: https://textq.audkenni.is:443/sso/
- Pending: Sigurður Másson to add prod redirect URI (https://alvitur.is/auth/callback)
- Live test pending: Sigvaldi prófunar SIM

## Handoff to Sprint 74

Aðal proposed scope: frontend auth flow (login UI + Valspjöld integration).
Carryover: Sprint 71/72 close tags missing (formal close needed retroactively).
