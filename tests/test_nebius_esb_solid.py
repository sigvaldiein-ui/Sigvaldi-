import os, httpx, json, asyncio, time, pprint

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL = {
    "DeepSeek-V4-Pro": "deepseek-ai/DeepSeek-V4-Pro",
    "Kimi-K2.6": "moonshotai/Kimi-K2.6",
    "GLM-5.2": "zai-org/GLM-5.2",
}

# Almennileg spurning – veikindaréttur
PROMPT = "Hvad segja islensk log um veikindarett? Svaradu a islensku."

async def test_model(client, name, model_id):
    print(f"\n{'='*60}")
    print(f"=== {name} ({model_id}) ===")
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 200,
        "temperature": 0.1,
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
    
    # Prenta ALLA lykla til að finna region/provider
    print(f"\nAllir lyklar i svari: {list(d.keys())}")
    
    if "choices" in d:
        content = d['choices'][0]['message'].get('content')
        if content:
            print(f"\nSvar:\n{content[:400]}")
        else:
            print("\n(TOMT SVAR)")
            print(f"Choice keys: {list(d['choices'][0].keys())}")
            if 'message' in d['choices'][0]:
                print(f"Message keys: {list(d['choices'][0]['message'].keys())}")
    else:
        print(f"\nVilla i svari:")
        pprint.pprint(d, indent=2, width=120, depth=3)
    
    return d

async def main():
    async with httpx.AsyncClient(timeout=90) as c:
        for name, mid in PANEL.items():
            try:
                await test_model(c, name, mid)
            except Exception as e:
                print(f"EXCEPTION: {e}")
    
    print(f"\n{'='*60}")
    print("LOKASKREF: Athugum ZDR og ESB stillingar")
    print("ATH: ZDR verdur ad vera kveikt i Nebius vidmotinu.")
    print("ESB-fani fyrir hvert model verdur ad vera stadfestur i vidmotinu.")
    print("Nidurstada: Krefst CTO stadfestingar a ESB-fana + ZDR.")
    print("="*60)

asyncio.run(main())
