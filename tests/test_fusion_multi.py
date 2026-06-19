import os, httpx, json, asyncio, time, sys
sys.path.insert(0, "/workspace/Sigvaldi-")

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL = {
    "GLM-5.2": ("zai-org/GLM-5.2", 4000),
    "Qwen3-235B": ("Qwen/Qwen3-235B-A22B-Instruct-2507", 500),
    "DeepSeek-V4-Pro": ("deepseek-ai/DeepSeek-V4-Pro", 500),
    "GPT-OSS-120B": ("openai/gpt-oss-120b", 500),
}
DÓMARI = ("deepseek-ai/DeepSeek-V4-Pro", 1000)

QUERIES = [
    "Hvað segja íslensk lög um veikindarétt?",
    "Hvaða reglur gilda um uppsögn starfsmanna á Íslandi?",
    "Hvað segja lög um persónuvernd á Íslandi?",
]

async def call_model(client, model_id, max_tok, system_prompt, user_msg):
    t0 = time.time()
    r = await client.post(f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model_id, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ], "max_tokens": max_tok, "temperature": 0.1}, timeout=180)
    t1 = time.time()
    d = r.json()
    content = ""
    if "choices" in d:
        content = d['choices'][0]['message'].get('content') or ""
    return {"model": model_id, "latency": (t1-t0)*1000, "content": content, "status": r.status_code}

async def run_query(query):
    print(f"\n{'='*60}")
    print(f"SPURNING: {query}")
    print(f"{'='*60}")
    from interfaces.chat_routes import _get_rag_context
    rag = await _get_rag_context(query, "legal")
    rag_text = rag.get("text", "")
    rag_citations = rag.get("citations", [])
    print(f"[RAG] Texti: {len(rag_text)} stafir, Heimildir: {len(rag_citations)}")

    system_prompt = (
        "Þú ert Alvitur — íslensk gervigreindarlausn. "
        "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
        "Tilgreindu alltaf heimildir.\n\n"
        f"HEIMILDIR:\n{rag_text}\n\nSvaraðu á íslensku."
    )
    user_msg = f"Spurning: {query}"

    async with httpx.AsyncClient(timeout=180) as c:
        tasks = [call_model(c, mid, mtok, system_prompt, user_msg) for mid, mtok in PANEL.values()]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(f"  {r['model']}: {r['status']} | {r['latency']:.0f}ms | {len(r['content'])} stafir")
        ok = [r for r in results if r["content"]]
        if len(ok) < 2:
            print("  [DÓMARI] Of fá svör")
            return
        answers_text = "\n\n".join([f"Svar {i+1} ({r['model']}):\n{r['content']}" for i, r in enumerate(ok)])
        judge_prompt = f"HEIMILDIR:\n{rag_text}\n\nSpurning: {query}\n\n{answers_text}\n\nSmíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar úr HEIMILDUM. Svaraðu á íslensku."
        dómari = await call_model(c, DÓMARI[0], DÓMARI[1], "Þú ert íslenskur lögfræðidómari.", judge_prompt)
        print(f"  DÓMARI: {dómari['status']} | {dómari['latency']:.0f}ms")
        from interfaces.chat_routes import _validate_response
        is_valid, _ = _validate_response(dómari["content"], rag_citations)
        print(f"  GROUNDING: {is_valid}")
        total = max(r['latency'] for r in results) + dómari['latency']
        print(f"  HEILDARTÍMI: {total:.0f}ms")

async def main():
    t0 = time.time()
    for q in QUERIES:
        await run_query(q)
    print(f"\n{'='*60}")
    print(f"ALLS: {len(QUERIES)} spurningar á {(time.time()-t0):.0f} sek")
    print(f"{'='*60}")

asyncio.run(main())
