import os, httpx, json, asyncio, time

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL_A = {
    "GLM-5.2": "zai-org/GLM-5.2",
    "Qwen3-235B": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "DeepSeek-V4-Pro": "deepseek-ai/DeepSeek-V4-Pro",
}

PANEL_B = {
    "GLM-5.2": "zai-org/GLM-5.2",
    "Qwen3-235B": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "DeepSeek-V4-Pro": "deepseek-ai/DeepSeek-V4-Pro",
    "GPT-OSS-120B": "openai/gpt-oss-120b",
}

PROMPT = "Hvad segja islensk log um veikindarett? Svaradu a islensku og vitnadu i heimildir."

PRICING = {
    "zai-org/GLM-5.2": (1.40, 4.40),
    "Qwen/Qwen3-235B-A22B-Instruct-2507": (0.20, 0.60),
    "deepseek-ai/DeepSeek-V4-Pro": (1.75, 3.50),
    "openai/gpt-oss-120b": (0.15, 0.60),
}

async def test_model(client, name, model_id):
    max_tok = 1500 if "glm" in model_id.lower() else 400
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": max_tok,
        "temperature": 0.1,
    }
    t0 = time.time()
    r = await client.post(f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json=body)
    t1 = time.time()
    d = r.json()
    latency = (t1-t0)*1000
    in_price, out_price = PRICING.get(model_id, (0,0))
    usage = d.get("usage", {})
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    cost = (in_tok/1e6)*in_price + (out_tok/1e6)*out_price
    
    print(f"  {name}: {r.status_code} | {latency:.0f}ms | in={in_tok} out={out_tok} | ${cost:.5f}")
    if "choices" in d:
        content = d['choices'][0]['message'].get('content')
        if content:
            print(f"    {content[:200].strip()}")
        else:
            reason = d['choices'][0]['message'].get('refusal') or d['choices'][0].get('finish_reason','?')
            print(f"    (TOMT) finish_reason={reason}")
    else:
        print(f"    Villa: {json.dumps(d, indent=2)[:200]}")
    return {"name": name, "status": r.status_code, "latency": latency, "in_tok": in_tok, "out_tok": out_tok, "cost": cost, "has_content": bool("choices" in d and d['choices'][0]['message'].get('content'))}

async def run_panel(label, panel):
    print(f"\n{'#'*60}")
    print(f"# {label}")
    print(f"{'#'*60}")
    results = []
    async with httpx.AsyncClient(timeout=120) as c:
        tasks = [test_model(c, name, mid) for name, mid in panel.items()]
        results = await asyncio.gather(*tasks)
    total_cost = sum(r["cost"] for r in results)
    total_lat = max(r["latency"] for r in results)
    ok = sum(1 for r in results if r["has_content"])
    print(f"  SAMTALS: {ok}/{len(panel)} svör | max latency={total_lat:.0f}ms | kostnaður=${total_cost:.5f}")
    return results

async def main():
    print("="*60)
    print("A/B PRÓF — Fusion panel: 3 vs 4 módel")
    print("Spurning: " + PROMPT)
    print("="*60)
    
    await run_panel("PANEL A — 3 módel (án GPT)", PANEL_A)
    await run_panel("PANEL B — 4 módel (með GPT-OSS-120B)", PANEL_B)
    
    print("\n" + "="*60)
    print("ÁKVÖRÐUN CTO: Sjá gögn að ofan. Velja A eða B.")
    print("="*60)

asyncio.run(main())
