import os, httpx, asyncio, time

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL_SVÖR = """Svar 1 (GLM-5.2): Íslensk lög um veikindarétt byggja aðallega á lögum um rétt verkafólks til launa vegna sjúkdóms- og slysaforfalla nr. 19/1979, og lögum um réttindi og skyldur starfsmanna ríkisins nr. 70/1996.
Svar 2 (Qwen3-235B): Samkvæmt 5. gr. laga nr. 45/2007 um útsenda starfsmenn á starfsmaður rétt til launa í veikinda- og slysatilvikum.
Svar 3 (DeepSeek-V4): Lög um útsenda starfsmenn kveða á um rétt til launa í veikindum. Einnig lög um réttindi starfsmanna ríkisins nr. 70/1996, 12. gr.
Svar 4 (GPT-OSS-120B): Tafla: nr. 45/2007 (útsendir starfsmenn), nr. 70/1996 (ríkisstarfsmenn), nr. 19/1979 (almennur réttur verkafólks)."""

RAG_TEXT = """• Lög um rétt verkafólks til uppsagnarfrests og launa vegna sjúkdóms- og slysaforfalla 1979 nr. 19
• Lög um útsenda starfsmenn og skyldur erlendra þjónustuveitenda 2007 nr. 45: 5. gr. Réttur til launa í veikinda- og slysatilvikum.
• Lög um réttindi og skyldur starfsmanna ríkisins 1996 nr. 70: 12. gr. Starfsmenn skulu eiga rétt til launa í veikindaforföllum."""

JUDGES = [
    ("DeepSeek-V4", "deepseek-ai/DeepSeek-V4-Pro", 800),
    ("GPT-OSS-120B", "openai/gpt-oss-120b", 800),
    ("GLM-5.2", "zai-org/GLM-5.2", 800),
    ("Qwen3-235B", "Qwen/Qwen3-235B-A22B-Instruct-2507", 800),
]

async def test_one(client, name, model_id, max_tok):
    prompt = f"HEIMILDIR:\n{RAG_TEXT}\n\nSpurning: Hvað segja íslensk lög um veikindarétt?\n\n{PANEL_SVÖR}\n\nSmíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar úr HEIMILDUM. Svaraðu á íslensku."
    try:
        t0 = time.time()
        r = await client.post(f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model_id, "messages": [
                {"role": "system", "content": "Þú ert íslenskur lögfræðidómari."},
                {"role": "user", "content": prompt}
            ], "max_tokens": max_tok, "temperature": 0.1}, timeout=180)
        t1 = time.time()
        d = r.json()
        latency = (t1-t0)*1000
        content = ""
        if "choices" in d:
            content = d['choices'][0]['message'].get('content') or ""
        return {"name": name, "ok": True, "latency": latency, "len": len(content), "content": content[:250]}
    except Exception as e:
        return {"name": name, "ok": False, "latency": 0, "len": 0, "content": str(e)[:120]}

async def main():
    print("="*60)
    print("DÓMARA-SAMANBURÐUR (öruggur)")
    print("="*60)
    async with httpx.AsyncClient(timeout=180) as c:
        for name, mid, mtok in JUDGES:
            result = await test_one(c, name, mid, mtok)
            if result["ok"]:
                print(f"\n{name}: {result['latency']:.0f}ms | {result['len']} stafir")
                print(f"  {result['content'][:200]}")
            else:
                print(f"\n{name}: FELL — {result['content'][:120]}")

asyncio.run(main())
