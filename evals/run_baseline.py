#!/usr/bin/env python3
"""Sprint 84 — Evals Harness v1. Keyrir 30 fyrirspurnir og reiknar 5 mælikvarða."""
import json, sys, time, os
import httpx

BASE_URL = os.environ.get("EVAL_BASE_URL", "http://localhost:8003")
API_ENDPOINT = f"{BASE_URL}/api/chat"
BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline_v1.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), f"results_{time.strftime('%Y%m%d_%H%M%S')}.json")

async def run_query(client, query, tier=None):
    payload = {"query": query}
    if tier:
        payload["tier"] = tier
    start = time.time()
    try:
        resp = await client.post(API_ENDPOINT, json=payload, timeout=120)
        elapsed = time.time() - start
        data = resp.json()
        return {
            "success": data.get("success", False),
            "citations_count": len(data.get("citations", [])),
            "pipeline_source": data.get("pipeline_source", ""),
            "tier": data.get("tier", ""),
            "response_len": len(data.get("response", "")),
            "latency_ms": round(elapsed * 1000),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000),
        }

async def main():
    with open(BASELINE_FILE) as f:
        baseline = json.load(f)
    
    results = []
    async with httpx.AsyncClient() as client:
        for i, q in enumerate(baseline["queries"], 1):
            print(f"  [{i}/30] {q['query'][:60]}...", end=" ", flush=True)
            r = await run_query(client, q["query"], q.get("tier"))
            r["id"] = q["id"]
            r["category"] = q["category"]
            r["query"] = q["query"]
            results.append(r)
            print(f"ok={r['success']} cites={r.get('citations_count',0)} {r.get('latency_ms',0)}ms")
    
    # Reikna mælikvarða
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    citation_precision = sum(r["citations_count"] > 0 for r in results) / total * 100
    grounding_rate = sum(1 for r in results if r["citations_count"] > 0 and r["success"]) / max(successful, 1) * 100
    
    vitinn = [r for r in results if r.get("tier") == "vitinn"]
    vault = [r for r in results if r.get("tier") == "vault"]
    vitinn_latency = sorted([r["latency_ms"] for r in vitinn])
    vault_latency = sorted([r["latency_ms"] for r in vault])
    
    p95 = lambda xs: xs[int(len(xs) * 0.95)] if xs else 0
    
    metrics = {
        "total_queries": total,
        "successful": successful,
        "citation_precision_rate_pct": round(citation_precision, 1),
        "grounding_rate_pct": round(grounding_rate, 1),
        "hallucination_rate_pct": "manual_review_required",
        "document_parsing_success_rate_pct": "deferred_sprint86",
        "latency": {
            "vitinn_median_ms": sorted(vitinn_latency)[len(vitinn_latency)//2] if vitinn_latency else 0,
            "vitinn_p95_ms": p95(vitinn_latency),
            "vault_median_ms": sorted(vault_latency)[len(vault_latency)//2] if vault_latency else 0,
            "vault_p95_ms": p95(vault_latency),
        },
    }
    
    report = {
        "baseline": baseline["description"],
        "date": time.strftime("%Y-%m-%d"),
        "metrics": metrics,
        "results": results,
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Results ===")
    print(f"Total: {total}, Successful: {successful}")
    print(f"Citation Precision Rate: {metrics['citation_precision_rate_pct']}%")
    print(f"Grounding Rate: {metrics['grounding_rate_pct']}%")
    print(f"Vitinn median latency: {metrics['latency']['vitinn_median_ms']}ms")
    print(f"Vault median latency: {metrics['latency']['vault_median_ms']}ms")
    print(f"\nReport saved to: {RESULTS_FILE}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
