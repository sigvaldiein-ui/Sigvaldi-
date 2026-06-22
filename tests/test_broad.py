import os, httpx, asyncio, time, sys, json

sys.path.insert(0, '/workspace/Sigvaldi-')

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"

PANEL = {
    "GLM-5.2": ("zai-org/GLM-5.2", 2000),
    "Qwen3-235B": ("Qwen/Qwen3-235B-A22B-Instruct-2507", 500),
    "DeepSeek-V4-Pro": ("deepseek-ai/DeepSeek-V4-Pro", 500),
    "GPT-OSS-120B": ("openai/gpt-oss-120b", 500),
}
DÓMARI = ("openai/gpt-oss-120b", 800)

QUERIES = [
    "Hvað segja íslensk lög um veikindarétt?",
    "Hvaða reglur gilda um uppsögn starfsmanna á Íslandi?",
    "Hvað segja lög um persónuvernd á Íslandi?",
    "Hvaða rétt hefur leigjandi gagnvart leigusala?",
    "Hvernig er háskólamenntun fjármögnuð á Íslandi?",
    "Hvaða reglur gilda um skattlagningu fyrirtækja?",
    "Hvað er þjóðaratkvæðagreiðsla og hvernig fer hún fram?",
    "Hvaða lög gilda um umhverfismál á Íslandi?",
    "Hver er munurinn á hlutafélagi og einkahlutafélagi?",
    "Hvaða reglur gilda um kosningar til Alþingis?",
]

async def call_model(client, model_id, max_tok, system_prompt, user_msg):
    try:
        t0 = time.time()
        r = await client.post(f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model_id, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ], "max_tokens": max_tok, "temperature": 0.1}, timeout=120)
        t1 = time.time()
        d = r.json()
        content = ""
        if "choices" in d:
            content = d['choices'][0]['message'].get('content') or ""
        return {"model": model_id, "latency": (t1-t0)*1000, "content": content, "status": r.status_code}
    except:
        return {"model": model_id, "latency": 0, "content": "", "status": 0}

async def run_query(query):
    from interfaces.chat_routes import _get_rag_context, _validate_response
    rag = await _get_rag_context(query, "legal")
    rag_text = rag.get("text", "")
    rag_citations = rag.get("citations", [])

    system_prompt = (
        "Þú ert Alvitur — íslensk gervigreindarlausn. "
        "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
        "Tilgreindu alltaf heimildir.\n\n"
        f"HEIMILDIR:\n{rag_text}\n\nSvaraðu á íslensku."
    )
    user_msg = f"Spurning: {query}"

    async with httpx.AsyncClient(timeout=120) as c:
        tasks = [call_model(c, mid, mtok, system_prompt, user_msg) for mid, mtok in PANEL.values()]
        results = await asyncio.gather(*tasks)
        ok = [r for r in results if r["content"]]
        if len(ok) < 2:
            return {"query": query, "grounding_ok": False, "total_time": 0, "num_models": len(ok), "citations": len(rag_citations)}
        answers_text = "\n\n".join([f"Svar {i+1} ({r['model']}):\n{r['content']}" for i, r in enumerate(ok)])
        judge_prompt = f"HEIMILDIR:\n{rag_text}\n\nSpurning: {query}\n\n{answers_text}\n\nSmíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar og laganúmer sem standa BERORÐUM í HEIMILDUM. Ef greinarnúmer vantar, tilgreindu þá bara lagið án greinar. Svaraðu á íslensku."
        dómari = await call_model(c, DÓMARI[0], DÓMARI[1], "Þú ert íslenskur lögfræðidómari.", judge_prompt)
        is_valid, _ = _validate_response(dómari["content"], rag_citations)
        total_time = max(r['latency'] for r in results) + dómari['latency']
        print(f"  {query[:50]:50s} | grounding={is_valid} | time={total_time:.0f}ms | models={len(ok)} | citations={len(rag_citations)}")
        return {"query": query, "grounding_ok": is_valid, "total_time": total_time, "num_models": len(ok), "citations": len(rag_citations)}

async def main():
    print("="*80)
    print("BREIDDARPRÓF – 10 íslenskar spurningar")
    print("="*80)
    print(f"  {'Spurning':50s} | Gr. | Tími    | Mdl | Heim.")
    print("-"*80)
    
    tasks = [run_query(q) for q in QUERIES]
    results = await asyncio.gather(*tasks)
    
    total = len(results)
    ok = sum(1 for r in results if r["grounding_ok"])
    times = [r["total_time"] for r in results if r["total_time"] > 0]
    avg_time = sum(times)/len(times) if times else 0
    max_time = max(times) if times else 0
    min_time = min(times) if times else 0
    
    print("-"*80)
    print(f"\nSAMANTEKT:")
    print(f"  Spurningar: {total}")
    print(f"  grounding_ok = True: {ok}/{total} ({100*ok/total:.0f}%)")
    print(f"  Meðaltími: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
    print(f"  Minnsti tími: {min_time:.0f}ms")
    print(f"  Mesti tími: {max_time:.0f}ms")

asyncio.run(main())
