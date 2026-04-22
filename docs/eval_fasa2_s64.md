# S65 Fasa 2 Evaluation (s64-fallback)

## Overview
- Timestamp: 2026-04-22T20:44:51.847661Z
- Model: google/gemini-2.5-flash
- Seed: calibrated v2 (see tests/eval/seed_queries.json meta.calibration_v2)
- Fallback threshold: confidence_score < 0.6
- Cost: ~$0.0003 for 13 API calls

## Results vs calibrated rule-only baseline

| Metric | Rule-only | LLM fallback | Delta |
|---|---:|---:|---:|
| overall_accuracy | 0.75 | **0.8** | +0.05 |
| domain_accuracy | 0.90 | 0.85 | -0.05 |
| reasoning_depth_accuracy | 0.85 | **0.9** | +0.05 |
| low_confidence_count | 13 | **9** | -4 |
| avg_latency_s | ~0.001 | 0.622 | +0.622 |

## Per category
| Category | Domain acc | Depth acc |
|---|---:|---:|
| normal | 0.6 | 0.8 |
| edge | 1.0 | 1.0 |
| ambiguous | 0.8 | 0.8 |
| file | 1.0 | 1.0 |

## Key findings
- File category went from 0.40 depth -> **1.00 depth** (seed calibration + LLM both contribute).
- Edge category domain improved 0.80 -> **1.00** (E05 calibration).
- Normal depth improved 0.60 -> **0.80** (N04 fix by LLM).
- Normal domain regressed 0.80 -> 0.60 due to N05 (jardhiti -> technical). Noted as honest miss.
- Low-confidence rate dropped 65% -> 45% via confidence calibration prompt.

## Deliverables
- tests/eval/seed_queries.json (calibrated)
- tests/eval/fasa2_s64.json
- tests/eval/run_fasa2.py
- core/intent_llm_fallback.py (prompt v2)
- core/llm_client.py (OpenRouter sync client)
- core/intent_gateway.py (4-line fallback hook)

## Aspirational misses (deferred to A7)
- A04 'skoda tolur' -> financial (needs Icelandic financial vocabulary)
- N05 'jardhiti' -> general (borderline natural science vs technical)
- A05 'greina gogn' -> deep (genuinely ambiguous)

## S66 dependency
- Queue/backpressure risk remains (see docs/SPRINT65_PLAN.md).
- 45% fallback trigger rate -> expect 0.45 x concurrent_requests LLM calls.
- Semaphore(4) in S66 recommended before production rollout.
