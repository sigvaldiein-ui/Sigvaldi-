# Sprint 66 — Track B Design: Live Intent Evaluation

**Status**: Draft (approved-in-principle by Sigvaldi 2026-04-23 ~11:30 GMT)
**Principal advisor**: Per (Claude Opus 4.7)
**Architect**: Opus (reviewing)
**Executor**: Sigvaldi
**Dependencies**: S66 pre-A (f52f6b7), S66 Track A (69e09e5)

## 1. Context

Track A landed an LLM concurrency guard around `call_openrouter`. Track B is
the *companion*: systematic measurement of intent classification quality
against real usage patterns. Motivating evidence is in S66 postmortem
(Opus Appendix): the IPv6 user at 06:42 GMT triggered end-to-end validation
by accident. Track B turns accidents into a process.

Sprint 65 Fasa 1 (baseline, f63) and Fasa 2 (fallback-on, f64) already
established the eval scaffolding in `tests/eval/`. Track B = **Fasa 3**:
production-faithful eval with precision/recall per domain, confusion
matrix, and live-log aggregation.

## 2. Current state (Discovery findings)

### Finding #0 — Taxonomy mismatch (MUST address in design, not code)

Three components use three different domain lists:

| Component | Classes |
|---|---|
| `models/intent.py` (Sprint 64 A2, frozen) | legal, financial, general, technical, public |
| `core/intent_gateway.py` | matches `models/intent.py` (canonical) |
| `interfaces/skills/classify.py` (Sprint 56) | legal, finance, writing, research, general |
| `interfaces/specialist_prompts.py` (Sprint 53a/56) | legal, finance, writing, research, general |

**Canonical decision**: `models/intent.py` is authoritative (newest,
frozen Pydantic, feeds Supervisor). ClassifySkill + specialist_prompts
reconciliation is **out of Track B scope** → follow-up S67-taxonomy.

### Finding #1 — Production traffic skews heavily "general"

Live `[INTENT]` log (34 entries as of 10:32 GMT 2026-04-23):
- All observed requests: `domain=general`, `depth=fast`, `conf=0.45–0.50`
- `adapter=None`, `src=text` (all chat, no file uploads in this window)
- No `INTENT_LLM_FALLBACK_ENABLED` in prod → rule-based only path

This is a **measurement blind spot**: we cannot distinguish "classifier
is correctly saying general" from "classifier is defaulting to general
under uncertainty".

### Finding #2 — Seed set coverage gaps

`tests/eval/seed_queries.json`:
- 20 queries, 4 categories (normal, edge, ambiguous, file), 5 each
- Domain coverage: 15 general + 5 financial
- **Missing**: zero queries for legal, technical, public → 3 of 5
  canonical domains untested

### Finding #3 — Fasa 2 baseline (what Track B must beat or match)

From `tests/eval/fasa2_s64.json` (gemini-2.5-flash fallback on):
- overall_accuracy: 0.80
- domain_accuracy: 0.85
- reasoning_depth_accuracy: 0.90
- low_confidence_pct: 0.45
- avg_latency_s: 0.622

Fasa 1 baseline (fallback off, `baseline_s63.json`):
- overall_accuracy: 0.55, depth_accuracy: 0.70
- **Delta Fasa 1 → Fasa 2: +25pp overall, driven by depth (+20pp)**

## 3. Scope

### B1 — Taxonomy reconciliation (documentation only)

- This document records the 3-way mismatch (Finding #0)
- Canonical = `models/intent.py`
- File S67 issue to align ClassifySkill + specialist_prompts
- **No code changes in Track B**

### B2 — Seed augmentation + Fasa 3 harness

Files:
- `tests/eval/seed_queries.json` → v2 with +20 Icelandic live-informed
  queries (chat general patterns) + 15 new (5 legal, 5 technical, 5 public)
  → total n=55
- `tests/eval/run_fasa3.py` — mirrors `run_fasa2.py` with:
  - `INTENT_LLM_FALLBACK_ENABLED` = **OFF by default** (measures prod as-is)
  - Adds precision + recall per domain
  - Adds confusion matrix (5×5 JSON)
  - Output: `tests/eval/fasa3_s66_{YYYY-MM-DD}.json`
- Second run with fallback ON for comparison → `fasa3_s66_fallback_{date}.json`

### B3 — Production log aggregator (zero PII)

File: `eval/intent_log_aggregate.py`
- Parses `[INTENT]` lines from `/workspace/web_server.log` + `logs/web_server.log`
- Aggregates (no raw queries, no IPs):
  - Count per `endpoint × domain × depth`
  - Confidence distribution (buckets: <0.5, 0.5-0.6, 0.6-0.8, 0.8-1.0)
  - Adapter usage count
  - Source distribution (text/pdf/xlsx/...)
- Output: `eval/intent_live_stats_{YYYY-MM-DD}.json`

### B4 — Scheduled eval + alert (DEFERRED to after S71.5)

Cron-based daily run of B2 + B3, Telegram alert if regression > 5pp
in any domain. Requires IP hashing (S71.5) before broader data capture.

## 4. Success criteria

Track B MVP is "done" when all four hold:

1. `docs/s66_b_design.md` committed (this file)
2. `tests/eval/run_fasa3.py` runs clean and produces two JSON artifacts
   (fallback-off baseline + fallback-on comparison), both committed
3. `eval/intent_log_aggregate.py` produces one aggregate artifact from
   current logs, committed
4. Tag `s66-b-baseline` applied to the commit containing the above

## 5. Non-goals

- Fix taxonomy mismatch (belongs in S67)
- Log raw user queries (blocked on S71.5 IP hashing / GDPR review)
- Dashboard UI (Telegram text alerts are enough for MVP)
- Multi-turn / contextual intent (flat per-query for now)
- Change production classifier behavior (Track B is *measurement only*)

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Fallback-off baseline looks "worse" than Fasa 2 → false regression signal | Report both fallback-off and fallback-on. Fasa 3 = prod-faithful, not Fasa-2 comparison |
| Seed augmentation injects rater bias (Per+Sigvaldi label queries) | Use expected_domain from keyword rules when unambiguous; mark uncertain items as `category: ambiguous` explicitly |
| Live log contains no raw query, limiting calibration | Track B3 scope capped at aggregate stats only; deeper live eval deferred to S71.5+ |
| Taxonomy mismatch causes Fasa 3 results to conflict with ClassifySkill downstream | Pin Fasa 3 to `classify_intent()` from `intent_gateway`. ClassifySkill path is orthogonal, measured separately in S67 |
| Adding 35 new seed queries changes Fasa 2 rerun numbers (not apples-to-apples) | Keep old 20 + new 35 as a superset. Report metrics on old-20 subset for historical comparison |

## 7. Execution plan (blocks after this doc is committed)

| Block | Deliverable | Est. time |
|---|---|---|
| BD (this) | Design doc committed | done |
| B3-code | `eval/intent_log_aggregate.py` + one artifact | 30 min |
| B2-seed | seed_queries.json v2 (+35 queries, hand-labeled) | 45 min |
| B2-harness | `tests/eval/run_fasa3.py` + precision/recall/confusion | 60 min |
| B2-run | Two runs (fallback off, on) + commit artifacts | 20 min |
| B-tag | Tag `s66-b-baseline` + push | 5 min |

Total MVP: ~2h40m of focused work.

## 8. Open questions for Opus review

1. Should Track B scope include adding **confidence calibration** (ECE /
   Brier score), or is that S68 work?
2. Is fallback-off the right default for Fasa 3, or should we mirror
   production (which today is fallback-off) regardless of what's right?
3. Should the new seed queries be in the same JSON or a separate
   `seed_queries_v2.json` to preserve Fasa 1/2 reproducibility?

---

**Commit anchor**: to be filled on commit (see S66 postmortem pattern).
