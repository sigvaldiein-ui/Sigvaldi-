# Sprint 88 — Plan

## Task 1 — D+1 guard tying

Implement `_validate_response` and `_build_deterministic_fallback`
in `interfaces/chat_routes.py` per Opus 4.7 architectural ruling
(18. maí 2026).

### Scope
- Enforce URL whitelist against citations array.
- Block hallucinated source names such as:
  - "Íslandsbanki"
  - "Statistíðna"
  - "statsfræðilög"
- Log all guard rejections in audit JSONL for future analysis.

### Acceptance
Canary query:
- "Hver er íbúafjöldi á Íslandi 2026?"

Expected:
- Response uses Hagstofa figure with year-tag (≈394.324).
- No mentions of "Íslandsbanki", "Statistíðna" or "statsfræðilög".
- All URLs in response must appear in the citations array.
