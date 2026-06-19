import httpx, os, asyncio, json

OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OR_KEY:
    print("VILLA: OPENROUTER_API_KEY ekki sett")
    exit(1)

async def test_esb():
    async with httpx.AsyncClient(timeout=30) as c:
        # --- JÁKVÆÐA PRÓF: DeepSeek á Nebius ---
        print("=== PRÓF 1: DeepSeek + Nebius pin ===")
        body = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": "Segðu halló á íslensku."}],
            "provider": {"only": ["Nebius"], "allow_fallbacks": False},
            "max_tokens": 30
        }
        r = await c.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_KEY}"},
            json=body)
        d = r.json()
        print("Status:", r.status_code)
        print("Lykillisti:", list(d.keys()))
        print("Provider:", d.get("provider"))
        print("Model info:", json.dumps(d.get("model_info", {}), indent=2))
        if "choices" in d:
            print("Svar:", d["choices"][0]["message"]["content"][:100])

        # --- PRÓF 2: Lesa provider með generation API ---
        print("\n=== PRÓF 2: Generation API (provider_name) ===")
        gen_id = d.get("id")
        if gen_id:
            r2 = await c.get(f"https://openrouter.ai/api/v1/generation?id={gen_id}",
                headers={"Authorization": f"Bearer {OR_KEY}"})
            gd = r2.json()
            print("Generation data keys:", list(gd.keys()))
            print("Provider name:", gd.get("provider_name"))
            print("Country:", gd.get("country"))
        else:
            print("Ekkert generation id — sleppa")

        # --- NEIKVÆÐA PRÓF: OpenAI pin → á að villa ---
        print("\n=== PRÓF 3: DeepSeek + OpenAI pin (á að villa) ===")
        body3 = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": "Halló"}],
            "provider": {"only": ["OpenAI"], "allow_fallbacks": False},
            "max_tokens": 30
        }
        r3 = await c.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_KEY}"},
            json=body3)
        print("Status:", r3.status_code)
        if r3.status_code >= 400:
            print("Villa (eins og vænst):", r3.json().get("error", {}).get("message", r3.text)[:200])
        else:
            d3 = r3.json()
            print("ÓVÆNT — routing tókst:", d3.get("provider"))

asyncio.run(test_esb())
