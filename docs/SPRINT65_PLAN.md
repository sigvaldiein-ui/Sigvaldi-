# Sprint 65 - The Supervisor Awakens

Branch: sprint65-supervisor
Baseline: main @ v0.65-baseline
DEV port: 8003
PROD port: 8000 (read-only until CTO go)

Phases:
- Phase 0 Safety rails
- Phase 1 Discovery (read-only, no installs)
- Phase 2 Supervisor core
- Phase 3 Self-correction and stats
- Phase 4 Merge and close

CTO constraints (2026-04-22):
- No PROD change until supervisor is feature-flagged AND smoke green AND CTO approves.
- SUPERVISOR_ENABLED defaults to false.

Hard gates:
- Read before write.
- Smoke monotonicity 11 -> 13 -> 15 -> 17.
- ASCII-only code.

---

## RISK (logged 2026-04-22, S65 F1 A6): No request queue / backpressure

- FastAPI uvicorn handles concurrency but no LLM throttle.
- 120s client timeout + OpenRouter 429 is only defense.
- S65 Supervisor + self-correction multiply LLM calls.
- Concurrency spike = 429 storm = broken UX.

### Mitigation (deferred to S66)
- asyncio.Semaphore(4) on LLM calls in web_server.py.
- In-memory FIFO with job-id + /api/jobs/<id> polling.
- No Redis/Celery (overkill for Iceland-scale).

### Evidence
- .bak-queue-0607 files from June 7 suggest prior attempt — review before S66 design.
- No celery/rq/dramatiq/arq/asyncio.Queue in repo today (verified via grep).
- No queue-related commits in git log.
