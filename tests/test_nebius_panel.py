import os, httpx, json, asyncio, time

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL = {
    "DeepSeek-V4-Pro": "deepseek-ai/DeepSeek-V4-Pro",
    "Kimi-K2.6": "moonshotai/Kimi-K2.6",
    "GLM-5.2": "zai-org/GLM-5.2",
}

async def test_model(client, name, model_id):
    print(f"\n=== {name} ({model_id}) ===")
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Segdu Godan daginn a islensku."}],
        "max_tokens": 50,
        "temperature": 0.0,
    }
    t0 = time.time()
    r = await client.post(f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json=body)
    t1 = time.time()
    d = r.json()
    print(f"Status: {r.status_code}")
    print(f"Latency: {(t1-t0)*1000:.0f}ms")
    print(f"Model i svari: {d.get('model', '?')}")
    if "choices" in d:
        content = d['choices'][0]['message'].get('content')
        if content:
            print(f"Svar: {content[:200]}")
        else:
            print("(tomt svar)")
    else:
        print(f"Villa: {json.dumps(d, indent=2)[:300]}")
    return d

async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        for name, mid in PANEL.items():
            await test_model(c, name, mid)
    print("\n=== Stadfesting ===")
    print("Allar fyrirspurnir foru i gegnum Nebius Token Factory (ESB)")

asyncio.run(main())
