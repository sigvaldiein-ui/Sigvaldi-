#!/usr/bin/env python3
"""
Sprint 66 Track B2 — Fasa 3 live intent eval harness.

Extends Fasa 2 (run_fasa2.py) with:
  - Runs on full seed_queries.json (all fasa levels, n=40)
  - Precision / recall / F1 per canonical domain
  - 5x5 confusion matrix (expected_domain vs actual_domain)
  - Per-category AND per-fasa metrics
  - Latency p50 / p95 / total
  - Respects INTENT_LLM_FALLBACK_ENABLED env (both modes supported)

Usage:
  INTENT_LLM_FALLBACK_ENABLED=0 python3 tests/eval/run_fasa3.py
  INTENT_LLM_FALLBACK_ENABLED=1 python3 tests/eval/run_fasa3.py

Output: tests/eval/fasa3_s66_{off|on}_{YYYY-MM-DD}.json
"""
from __future__ import annotations

import json
import os
import pathlib
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

# Auto-load /workspace/.env so OPENROUTER_API_KEY is available
# without requiring caller to `source .env` in shell.
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv('/workspace/.env')
except ImportError:
    pass  # dotenv optional; shell-source still works

# Repo-root on sys.path so `core` is importable regardless of CWD/caller.
import sys as _sys, pathlib as _pathlib
_REPO_ROOT = _pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from core.intent_gateway import classify_intent

CANONICAL_DOMAINS = ["legal", "financial", "general", "technical", "public"]


def p_q(xs, q):
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = int(round(q * (len(xs) - 1)))
    return xs[k]


def main() -> int:
    fallback_on = os.getenv("INTENT_LLM_FALLBACK_ENABLED", "").lower() in (
        "1", "true", "yes", "on")
    if fallback_on:
        assert os.getenv("OPENROUTER_API_KEY"), \
            "OPENROUTER_API_KEY required when fallback is ON"

    seed_path = pathlib.Path("tests/eval/seed_queries.json")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    queries = seed["queries"]

    rows = []
    latencies = []
    for q in queries:
        t0 = time.perf_counter()
        r = classify_intent(
            query=q.get("query"),
            filename=q.get("filename"),
            file_size=q.get("file_size"),
        ).model_dump()
        dt = time.perf_counter() - t0
        latencies.append(dt)
        rows.append({
            "id": q["id"],
            "category": q["category"],
            "fasa": q.get("fasa", 1),
            "expected_domain": q["expected_domain"],
            "expected_depth": q["expected_depth"],
            "actual_domain": r["domain"],
            "actual_depth": r["reasoning_depth"],
            "confidence": r["confidence_score"],
            "latency_s": round(dt, 3),
            "domain_ok": r["domain"] == q["expected_domain"],
            "depth_ok": r["reasoning_depth"] == q["expected_depth"],
        })

    n = len(rows)

    # Confusion matrix
    confusion = {e: {a: 0 for a in CANONICAL_DOMAINS}
                  for e in CANONICAL_DOMAINS}
    for r in rows:
        e = r["expected_domain"]
        a = r["actual_domain"]
        if e in confusion and a in confusion[e]:
            confusion[e][a] += 1

    # Per-domain precision / recall / F1
    per_domain = {}
    for d in CANONICAL_DOMAINS:
        tp = sum(1 for r in rows
                 if r["expected_domain"] == d and r["actual_domain"] == d)
        fp = sum(1 for r in rows
                 if r["expected_domain"] != d and r["actual_domain"] == d)
        fn = sum(1 for r in rows
                 if r["expected_domain"] == d and r["actual_domain"] != d)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_domain[d] = {
            "n_expected": sum(1 for r in rows if r["expected_domain"] == d),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
        }

    # Per-category breakdown
    categories = sorted({r["category"] for r in rows})
    per_category = {}
    for c in categories:
        sub = [r for r in rows if r["category"] == c]
        nc = len(sub)
        per_category[c] = {
            "n": nc,
            "domain_acc": round(sum(r["domain_ok"] for r in sub) / max(1, nc), 3),
            "depth_acc": round(sum(r["depth_ok"] for r in sub) / max(1, nc), 3),
        }

    # Per-fasa breakdown
    per_fasa = {}
    for f in sorted({r["fasa"] for r in rows}):
        sub = [r for r in rows if r["fasa"] == f]
        nf = len(sub)
        per_fasa[f"fasa_{f}"] = {
            "n": nf,
            "domain_acc": round(sum(r["domain_ok"] for r in sub) / max(1, nf), 3),
            "depth_acc": round(sum(r["depth_ok"] for r in sub) / max(1, nf), 3),
            "overall_acc": round(
                sum(r["domain_ok"] and r["depth_ok"] for r in sub) / max(1, nf), 3),
        }

    # Overall
    metrics = {
        "overall_accuracy": round(
            sum(r["domain_ok"] and r["depth_ok"] for r in rows) / n, 3),
        "domain_accuracy": round(sum(r["domain_ok"] for r in rows) / n, 3),
        "reasoning_depth_accuracy": round(sum(r["depth_ok"] for r in rows) / n, 3),
        "macro_f1": round(
            sum(per_domain[d]["f1"] for d in CANONICAL_DOMAINS) / len(CANONICAL_DOMAINS), 3),
        "low_confidence_count": sum(1 for r in rows if r["confidence"] < 0.6),
        "low_confidence_pct": round(
            sum(1 for r in rows if r["confidence"] < 0.6) / n, 3),
        "latency_p50_s": round(p_q(latencies, 0.50), 3),
        "latency_p95_s": round(p_q(latencies, 0.95), 3),
        "latency_total_s": round(sum(latencies), 2),
        "latency_avg_s": round(sum(latencies) / n, 3),
    }

    out = {
        "sprint": "S66",
        "artifact": f"Fasa 3 (fallback {'ON' if fallback_on else 'OFF'})",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "fallback_enabled": fallback_on,
        "fallback_model": os.getenv(
            "INTENT_LLM_FALLBACK_MODEL", "google/gemini-2.5-flash") if fallback_on else None,
        "n_queries": n,
        "canonical_domains": CANONICAL_DOMAINS,
        "metrics": metrics,
        "per_domain": per_domain,
        "confusion_matrix": confusion,
        "per_category": per_category,
        "per_fasa": per_fasa,
        "rows": rows,
    }

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    suffix = "on" if fallback_on else "off"
    out_path = pathlib.Path(f"tests/eval/fasa3_s66_{suffix}_{date_str}.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"wrote {out_path}: {out_path.stat().st_size} bytes")
    print("--- metrics ---")
    print(json.dumps(metrics, indent=2))
    print("--- per_domain ---")
    for d in CANONICAL_DOMAINS:
        pd = per_domain[d]
        print(f"  {d:10s} n={pd['n_expected']} "
              f"P={pd['precision']:.2f} R={pd['recall']:.2f} F1={pd['f1']:.2f}")
    print("--- confusion (row=expected, col=actual) ---")
    header = "  " + " ".join(f"{d[:4]:>5s}" for d in CANONICAL_DOMAINS)
    print(header)
    for e in CANONICAL_DOMAINS:
        cells = " ".join(f"{confusion[e][a]:>5d}" for a in CANONICAL_DOMAINS)
        print(f"  {e[:4]:4s} {cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
