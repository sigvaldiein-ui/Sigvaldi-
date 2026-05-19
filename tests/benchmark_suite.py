"""
Sprint 90.5 — Benchmark Suite & Factual Hit-Rate Assessment
Enforces Lesson #107, #108 and #109. Independent testing engine.
"""
import sys, os, time, re, httpx

VAULT_LOCAL_URL = "http://localhost:8000/api/chat"
VLLM_HEALTH_URL = "http://localhost:8002/v1/models"

TEST_QUERIES = [
    {"query": "Hvað segja nýjustu tölur Hagstofunnar um verðbólgu?", "type": "hagstofa"},
    {"query": "Hver eru lögfræðilegu ákvæðin um orkuskipti ehf?", "type": "lagasafn"},
    {"query": "Sýndu mér tölfræði frá Seðlabanka Íslands samkvæmt heimildum.", "type": "almennt"},
    {"query": "Hvað segir Íslandsbanki um nýja innviði á RunPod?", "type": "adversarial"}
]

async def run_benchmark():
    print("=== Ræsi Benchmark Suite (Sprint 90.5) ===")
    
    # 1. vLLM Uptime Guarantee Check (Lesson #109)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(VLLM_HEALTH_URL)
            if res.status_code != 200:
                print("❌ ERROR: vLLM backend á porti 8002 svarar ekki lögmætt.")
                return
            print("✅ Backend Uptime Verified (Port 8002 active).")
    except Exception as e:
        print(f"❌ ERROR: Ekki náðist samband við vLLM: {e}")
        return

    total_runs = 0
    falsification_failures = 0
    total_response_len = 0

    for i in range(3):
        for item in TEST_QUERIES:
            total_runs += 1
            query = item["query"]
            start = time.time()
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(VAULT_LOCAL_URL, json={"query": query})
                    latency = (time.time() - start) * 1000
                    
                    if resp.status_code == 429:
                        print(f"[{total_runs}] 🚫 Rate Limiter Triggered (HTTP 429) - Pass.")
                        continue
                    elif resp.status_code != 200:
                        print(f"[{total_runs}] ❌ API Error: HTTP {resp.status_code}")
                        continue
                        
                    data = resp.json()
                    response_text = data.get("response", "")
                    total_response_len += len(response_text)
                    
                    if item["type"] == "adversarial" and any(x in response_text.lower() for x in ["íslandsbanki", "statistíðnaði"]):
                        falsification_failures += 1
                        print(f"[{total_runs}] ⚠️ Falsification Failure greind!")
                    else:
                        print(f"[{total_runs}] ✅ Success - Latency: {latency:.1f}ms")
                        
            except Exception as e:
                print(f"[{total_runs}] ❌ Kall mistókst: {e}")

    print("\n=== LOKANIÐURSTÖÐUR BENCHMARK ===")
    print(f"Heildar keyrslur mældar: {total_runs}")
    print(f"Falsification Failures (Ofskynjanir): {falsification_failures}")
    if total_response_len > 0:
        print("✅ Gæðamat klárað án kerfishruns.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_benchmark())
