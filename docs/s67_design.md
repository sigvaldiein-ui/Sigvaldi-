# Sprint 67 — Design Doc

**Author**: Per (via Sigvaldi shell session)
**Reviewers**: Opus, Aðal
**Start**: 2026-04-23 post-lunch
**Predecessor**: `sprint66-closed` tag (all S66 deliverables shipped)

---

## 1. Context

Sprint 66 shipped empirical baseline for intent classification:
- OFF (rule-based): macro F1 = 0.71
- ON (gemini-2.5-flash fallback): macro F1 = 0.91

Gap = +20pp, driven overwhelmingly by `public` domain (F1 0.00 → 0.80).
Key bottleneck: `_score_keywords()` has no Icelandic public-service
vocabulary. Every `public` query falls to `general` or `financial`.

Additionally, Finding #7 (session 2026-04-23 BI block) revealed
silent exception swallow in `refine_with_llm`, masking failures for
hours during today's Fasa 3 run.

Sprint 67 addresses both issues and consolidates monitoring.

---

## 2. Goals (in priority order)

### G1. Close Finding #7 — verbose fallback logging
**Problem**: `core/intent_llm_fallback.py` lines 134-136, 140-142
have `except: return rule_result` with zero logging. Masked
authentication failures for 23 LLM calls on 2026-04-23.
**Change**: Inject `logger.warning(f"[INTENT-LLM] {op} failed: "
f"{type(e).__name__}: {e}")` before each fail-closed return.
**Impact**: Next time key is invalid, we see it in 1 log line
instead of wasting 30 min on metric forensics.

### G2. Expand `_score_keywords()` for Icelandic public domain
**Problem**: `public` F1 = 0.00 in OFF mode because rule-based
classifier has no public-service keywords. 4 of 5 public queries
fall to `general`, 1 to `financial` (RSK -> finance mistake).
**Change**: Add ~15 Icelandic keywords to `_KEYWORDS["public"]`:
  - ökuskírteini, vegabréf, kennitala, fæðingarorlof
  - RSK (disambiguation needed — also financial context)
  - skattskýrsla, skattkort
  - Þjóðskrá, þjóðskrárnúmer
  - sjúkratrygging, örorkubætur, ellilífeyrir
  - Vinnumálastofnun, atvinnuleysisbætur
  - vottorð, hjúskaparstaða
**Target**: public OFF F1 0.00 → 0.60+ on current seed.
**Measured by**: `run_fasa3.py` before/after diff.

### G3. Per-depth confusion matrix in harness
**Problem**: Current harness reports per-domain confusion but
depth classifier weakness (OFF 0.65) is opaque — we don't know
if `standard` maps to `fast`, `deep`, or scatter.
**Change**: Extend `run_fasa3.py` with `per_depth_confusion` 3x3
matrix (fast/standard/deep) in output JSON.
**Impact**: Data-driven prioritization of depth heuristic work.

## 3. Non-goals

- **No changes to classify_intent signature.** All changes are
  additive to `_score_keywords` and `refine_with_llm` internals.
- **No fine-tuning of gemini-flash prompts.** ON baseline is 0.91,
  good enough; focus is lifting OFF baseline toward ON.
- **No new LLM providers.** OpenRouter + gemini-2.5-flash fixed.
- **No Icelandic-specific NER.** Keyword expansion only; NER is
  S68+ scope.

## 4. Tracks

### Track A — Verbose fallback logging (G1)
- A1: Patch `core/intent_llm_fallback.py` with `logger.warning`
      before each `return rule_result` in `except` blocks.
- A2: Add `logger.info` on successful fallback invocation
      (model, latency_ms, result_domain) — matches `llm_client`
      logging style.
- A3: Smoke test: run with invalid key, verify warning appears.
- A4: Smoke test: run with valid key, verify info log on success.
- A5: Commit, tag `s67-a-fallback-logging`.
**Est**: 25 min. Low risk.

### Track B — Public keyword expansion (G2)
- B1: Read `core/intent_gateway.py` to find `_KEYWORDS` or
      equivalent dict and its current `public` entries.
- B2: Add ~15 Icelandic keywords (list in G2).
- B3: **Disambiguation**: "RSK" + "kostar" -> financial stays;
      "RSK" + "skráning" / "vottorð" -> public. Heuristic tuning.
- B4: Run `run_fasa3.py` fallback OFF, capture before/after delta.
- B5: If public F1 >= 0.60, commit + tag `s67-b-public-keywords`.
      If < 0.60, iterate on keyword set.
**Est**: 45 min. Medium risk (keyword collisions with financial).

### Track C — Per-depth confusion (G3)
- C1: Extend harness output JSON with `per_depth_confusion` key.
- C2: Re-run OFF baseline with new harness; commit artifact.
- C3: Analyze matrix, document depth weaknesses in report.
**Est**: 30 min. Low risk, read-only change.

### Track D (nice-to-have) — Pre-commit key leak guard
- D1: Add `.githooks/pre-commit` with `grep -E "sk-or-v1-[a-f0-9]{48,}"`
      against staged diff.
- D2: Install via `git config core.hooksPath .githooks`.
- D3: Smoke test: try commit with fake key, verify reject.
**Est**: 15 min. Skip if A+B+C run long.

## 5. Success Criteria

MVP closes when:
1. Track A committed + tagged.
2. Track B committed + tagged + measurable public F1 improvement.
3. Track C committed + new baseline artifact with depth confusion.
4. `docs/s67_final_report.md` captures numbers + Lessons #16+.

Stretch: Track D committed.

## 6. Risks

- **R1**: RSK disambiguation too fragile. Query "Hvad kostar RSK
  skráning?" could go public OR financial. Accept: pick one,
  document choice, defer ambiguity resolution to S68.
- **R2**: Keyword additions could regress `general` F1 (currently
  0.84 OFF). Monitor closely — if general drops below 0.80,
  rollback and use more targeted keyword patterns.
- **R3**: Session fatigue — post-lunch energy is limited.
  Use block-by-block, commit early, don't chain 3+ tracks.

## 7. Handoff

After sprint67-closed:
- S68 candidate: Fine-tune gemini-flash prompt for financial
  precision (currently 0.80, lowest of 5 domains)
- S68 candidate: Expand seed to n=80 for tighter confidence
  intervals on per-domain F1

