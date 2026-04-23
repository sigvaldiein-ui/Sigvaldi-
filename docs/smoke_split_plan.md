# Smoke Split Plan (Phase 1 A4, 2026-04-22)

## Current state
- tests/smoke.sh: 142 lines, 11 tests, full run ~54 seconds.
- Server-dependent (curl to :8003): T1-T8 (8 tests).
- Pure local adapter (python3 -c): T9, T10, T11 (3 tests).

## Timing by class
- Health/diagnostics (T1, T2, T3): curl max 5s each, ~<2s actual.
- Beta promotion + LLM (T4, T5, T6, T7, T8): curl max 120s each,
  actual run dominated by LLM latency.
- Adapter-only (T9, T10, T11): python subprocess, under 1s each.

## Target split

### smoke_fast.sh  (target: under 10 seconds)
- T1 health endpoint
- T2 diagnostics env
- T3 leid A enabled
- T9 PDF table extraction
- T10 DOCX table extraction
- T11 unified dispatcher happy path

Use case: pre-commit hook, fast sanity after small edits, feature-flag
toggle verification.

### smoke_full.sh  (target: under 2 minutes)
- All of smoke_fast plus T4, T5, T6, T7, T8.
- Current behaviour of tests/smoke.sh preserved.

Use case: before every commit/tag, merge gates, post-merge verification.

## Implementation notes for Phase 3 A-cleanup
- Extract shared header (BASE, PORT, pass/fail helpers) into
  tests/smoke_lib.sh sourced by both scripts.
- Keep tests/smoke.sh as an alias for smoke_full.sh during transition
  so existing workflows and SPRINT*.md references do not break.
- Add bash tests/smoke_fast.sh to developer docs as the default
  quick-check command.

## Do not split in Phase 1
- Discovery phase only. No changes to tests/smoke.sh yet.
- Actual split lands in Phase 3 alongside D1 /api/stats work.
