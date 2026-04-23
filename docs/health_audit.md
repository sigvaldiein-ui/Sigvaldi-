# Health Endpoint Audit (Phase 1 A5, 2026-04-22)

## Current definition
- File: interfaces/web_server.py
- Route: GET /api/health (line 2891)
- Pydantic model: lines 268-272 (version: str, fasi: str)

## Current payload (DEV 8003 and PROD 8000 identical)
{
  "status": "ok",
  "version": "sprint63-track-b",
  "timestamp": "<iso utc>",
  "fasi": "production"
}

## Issues
- version still reads "sprint63-track-b" even though Sprint 64 has
  been merged to main and tagged v0.64-complete.
- fasi reads "production" on BOTH DEV 8003 and PROD 8000.
  DEV should read "dev" so operators can distinguish instances.
- No supervisor_enabled flag surfaced, which will matter in S65
  once SUPERVISOR_ENABLED feature flag is introduced.

## Hardcoded sites
- Line 2896: "version": "sprint63-track-b" (primary health handler).
- Line 2919: "version": "sprint63-track-b" (second site, likely
  a duplicate route or legacy mirror, needs verification).

## Patch plan for Phase 3 A-cleanup
- Replace hardcoded string with a module-level constant:
    APP_VERSION = "sprint65-supervisor"
    SUPERVISOR_ENABLED = os.getenv("SUPERVISOR_ENABLED", "false")
- Pull fasi from ALVITUR_ENV env var so DEV shows "dev" and
  PROD shows "production".
- Extend health payload (additive, non-breaking):
    {
      "status": "ok",
      "version": APP_VERSION,
      "timestamp": "<iso>",
      "fasi": "<env>",
      "supervisor_enabled": <bool>
    }
- Keep response schema backward compatible: existing consumers
  only reading status/version/fasi continue to work.

## Do not patch in Phase 1
- Discovery only. Live patch lands in Phase 3 A-cleanup alongside
  smoke split and optional pymupdf4llm adoption.
