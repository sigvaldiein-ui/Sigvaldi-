#!/usr/bin/env python3
"""Sprint 84 — Keyrir 30 fyrirspurnir, 5 í einu, og vistar niðurstöður."""
import json, os, sys, time
import httpx

BASE_URL = os.environ.get("EVAL_BASE_URL", "http://localhost:8003")
API_ENDPOINT = f"{BASE_URL}/api/chat"
INPUT_FILE = os.path.join(os.path.dirname(__file__), "baseline_v1.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), f"results_chunked_{time.strftime('%Y%m%d_%H%M%S')}.json")

async def run_one(client, q):
    payload = {"query": q["query"]}
    if q.get("tier"):
        payload["tier"] = q["tier"]
    start = time.time()
    try:
        resp = await client.post(API_ENDPOINT, json=payload, timeout=90)
        elapsed = time.time() - start
        data = resp.json()
        return {
            "id": q["id"], "query": q["query"][:80],
            "success": data.get("success", False),
            "citations": len(data.get("citations", [])),
            "tier": data.get("tier", ""),
            "pipeline": data.get("pipeline_source", ""),
            "latency_ms": round(elapsed * 1000),
        }
    except Exception as e:
        return {
            "id": q["id"], "query": q["query"][:80],
            "success": False, "error": str(e),
            "latency_ms": round((time.time() - start) * 1000),
        }

async def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)
    queries = data["queries"]
    
    results = []
    async with httpx.AsyncClient() as client:
        for chunk_start in range(0, len(queries), 5):
            chunk = queries[chunk_start:chunk_start+5]
            tasks = [run_one(client, q) for q in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)
            
            # Sýna árangur eftir hvern skammt
            ok = sum(1 for r in chunk_results if r["success"])
            cites = sum(r.get("citations", 0) for r in chunk_results)
            print(f"  Skammtur {chunk_start//5 + 1}/6: {ok}/{len(chunk)} tókust, {cites} citations")
            
            # Vista eftir hvern skammt (öryggisvörn)
            with open(OUTPUT_FILE, "w") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # Stutt bið á milli skammta til að ofhlaða ekki kerfið
            if chunk_start + 5 < len(queries):
                await asyncio.sleep(3)
    
    # Reikna heildarniðurstöður
    total = len(results)
    ok = sum(1 for r in results if r["success"])
    with_cites = sum(1 for r in results if r.get("citations", 0) > 0)
    
    print(f"\n=== Heildarniðurstöður ===")
    print(f"Fyrirspurnir: {total}, Tókust: {ok}")
    print(f"Citation Precision Rate: {with_cites/total*100:.0f}% ({with_cites}/{total})")
    print(f"Niðurstöður vistaðar: {OUTPUT_FILE}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
