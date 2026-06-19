import os, httpx, json, asyncio, time

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PROMPT = "Hvad segja islensk log um veikindarett? Svaradu a islensku stuttlega."

THINKING_MODELS = {
    "GLM-5.2 (max_tokens=4000)": ("zai-org/GLM-5.2", 4000),
    "GLM-5.2 (max_tokens=2000)": ("zai-org/GLM-5.2", 2000),
    "GPT-OSS-120B (max_tokens=4000)": ("openai/gpt-oss-120b", 4000),
    "GPT-OSS-120B (max_tokens=2000)": ("openai/gpt-oss-120b", 2000),
}

async def test_model(client, label, model_id, max_tok):
    print(f"\n{'='*60}")
    print(f"=== {label} ===")
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
    
    if "choices" in d:
        finish = d['choices'][0].get('finish_reason', '?')
        content = d['choices'][0]['message'].get('content')
        reasoning = d['choices'][0]['message'].get('reasoning', '')[:100] if d['choices'][0].get('message', {}).get('reasoning') else ''
        in_tok = d.get('usage', {}).get('prompt_tokens', 0)
        out_tok = d.get('usage', {}).get('completion_tokens', 0)
        reasoning_tok = d.get('usage', {}).get('reasoning_tokens', 0)
        
        print(f"Status: {r.status_code} | Latency: {latency:.0f}ms | in={in_tok} out={out_tok} reason={reasoning_tok} | finish={finish}")
        
        if reasoning:
            print(f"Reasoning (fyrstu 200): {reasoning[:200]}")
        if content:
            print(f"\nSvar:\n{content[:600]}")
        else:
            print("(TOMT SVAR)")
    else:
        print(f"Villa: {json.dumps(d, indent=2)[:300]}")
    return d

async def main():
    print("="*60)
    print("THINKING-MÓDEL — GLM-5.2 & GPT-OSS-120B")
    print("Prófum mismunandi max_tokens")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=180) as c:
        for label, (mid, mtok) in THINKING_MODELS.items():
            try:
                await test_model(c, label, mid, mtok)
            except Exception as e:
                print(f"EXCEPTION: {e}")

asyncio.run(main())
