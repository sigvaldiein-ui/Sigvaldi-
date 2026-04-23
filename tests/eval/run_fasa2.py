"""
Sprint 65 Fasa 2 — run seed queries with LLM fallback ON.
Reads tests/eval/seed_queries.json, writes tests/eval/fasa2_s64.json.
Idempotent: safe to re-run (overwrites output JSON).
"""
import json, os, pathlib, time, datetime
# Repo-root on sys.path so `core` is importable regardless of CWD/caller.
import sys as _sys, pathlib as _pathlib
_REPO_ROOT = _pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

from core.intent_gateway import classify_intent

assert os.getenv("INTENT_LLM_FALLBACK_ENABLED", "").lower() in ("1","true","yes","on"), \
    "Set INTENT_LLM_FALLBACK_ENABLED=1 before running"
assert os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY must be set"

seed = json.loads(pathlib.Path("tests/eval/seed_queries.json").read_text())
rows, total_latency = [], 0.0

for q in seed["queries"]:
    t0 = time.time()
    r = classify_intent(
        query=q.get("query"),
        filename=q.get("filename"),
        file_size=q.get("file_size"),
    ).model_dump()
    dt = time.time() - t0
    total_latency += dt
    rows.append({
        "id": q["id"], "category": q["category"],
        "expected_domain": q["expected_domain"],
        "expected_depth": q["expected_depth"],
        "actual_domain": r["domain"],
        "actual_depth": r["reasoning_depth"],
        "confidence": r["confidence_score"],
        "latency_s": round(dt, 3),
        "domain_ok": r["domain"] == q["expected_domain"],
        "depth_ok": r["reasoning_depth"] == q["expected_depth"],
        "low_conf": r["confidence_score"] < 0.6,
    })

n = len(rows)
m = {
    "overall_accuracy": round(sum(r["domain_ok"] and r["depth_ok"] for r in rows)/n, 3),
    "domain_accuracy": round(sum(r["domain_ok"] for r in rows)/n, 3),
    "reasoning_depth_accuracy": round(sum(r["depth_ok"] for r in rows)/n, 3),
    "low_confidence_count": sum(r["low_conf"] for r in rows),
    "low_confidence_pct": round(sum(r["low_conf"] for r in rows)/n, 3),
    "total_latency_s": round(total_latency, 2),
    "avg_latency_s": round(total_latency/n, 3),
}
per_cat = {cat: {
    "n": sum(1 for r in rows if r["category"]==cat),
    "domain_acc": round(sum(r["domain_ok"] for r in rows if r["category"]==cat)
                         / max(1, sum(1 for r in rows if r["category"]==cat)), 3),
    "depth_acc":  round(sum(r["depth_ok"] for r in rows if r["category"]==cat)
                         / max(1, sum(1 for r in rows if r["category"]==cat)), 3),
} for cat in ["normal","edge","ambiguous","file"]}

out = {
    "sprint": "S65", "artifact": "Fasa 2 fallback on",
    "timestamp_utc": datetime.datetime.utcnow().isoformat()+"Z",
    "fallback_enabled": True,
    "model": os.getenv("INTENT_LLM_FALLBACK_MODEL","google/gemini-2.5-flash"),
    "n_queries": n, "metrics": m, "per_category": per_cat, "rows": rows,
}
pathlib.Path("tests/eval/fasa2_s64.json").write_text(json.dumps(out, indent=2))
print(json.dumps(m, indent=2))
print("per_category:", json.dumps(per_cat, indent=2))
