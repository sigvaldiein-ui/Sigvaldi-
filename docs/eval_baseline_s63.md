# S65 A6 Classifier Baseline (s63 tag)

- Timestamp: 2026-04-22T18:50:50.940289Z
- Queries: 20
- Target: core.intent_gateway.classify_intent (rule-based)

## Overall metrics
- Overall accuracy (domain AND depth): **0.55**
- Domain accuracy: **0.85**
- Reasoning depth accuracy: **0.7**
- Low-confidence count (<0.6): **13** (65%)
- Ambiguous->low-conf rate: **1.0**

## Per category
| Category | N | Domain acc | Depth acc |
|---|---:|---:|---:|
| normal | 5 | 0.8 | 0.6 |
| edge | 5 | 0.8 | 1.0 |
| ambiguous | 5 | 0.8 | 0.8 |
| file | 5 | 1.0 | 0.4 |

## Interpretation
- Rule-based classifier only emits {general, financial} and {fast, deep}.
- Ambiguous queries SHOULD be low-confidence; that rate is the trigger surface for S65 Fasa 2 LLM fallback.
- S65 Fasa 2 target: raise overall accuracy and REDUCE low-confidence count via LLM fallback while keeping latency bounded.

## Deliverables
- tests/eval/seed_queries.json
- tests/eval/baseline_s63.json
- docs/eval_baseline_s63.md (this file)
