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
