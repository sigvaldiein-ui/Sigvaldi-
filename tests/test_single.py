import os, httpx, asyncio, time, sys
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
    except Exception as e:
        return {"model": model_id, "latency": 0, "content": "", "status": str(e)[:50]}

async def main():
    query = "Hvað segja íslensk lög um veikindarétt?"
    print("="*60)
    print(f"STÖK AFKASTAMÆLING: {query}")
    print("="*60)
    
    from interfaces.chat_routes import _get_rag_context, _validate_response
    rag = await _get_rag_context(query, "legal")
    rag_text = rag.get("text", "")
    rag_citations = rag.get("citations", [])
    print(f"[RAG] {len(rag_text)} stafir, {len(rag_citations)} heimildir")
    
    system_prompt = (
        "Þú ert Alvitur — íslensk gervigreindarlausn. "
        "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
        "Tilgreindu alltaf heimildir.\n\n"
        f"HEIMILDIR:\n{rag_text}\n\nSvaraðu á íslensku."
    )
    user_msg = f"Spurning: {query}"
    
    t_start = time.time()
    async with httpx.AsyncClient(timeout=120) as c:
        tasks = [call_model(c, mid, mtok, system_prompt, user_msg) for mid, mtok in PANEL.values()]
        results = await asyncio.gather(*tasks)
        
        print("\nPANEL:")
        for r in results:
            has_content = "Já" if r["content"] else "Nei"
            print(f"  {r['model']}: {r['latency']:.0f}ms | svar={has_content} | status={r['status']}")
        
        ok = [r for r in results if r["content"]]
        if len(ok) < 2:
            print("\nOf fá svör til að keyra dómara.")
            return
        
        answers_text = "\n\n".join([f"Svar {i+1} ({r['model']}):\n{r['content']}" for i, r in enumerate(ok)])
        judge_prompt = f"HEIMILDIR:\n{rag_text}\n\nSpurning: {query}\n\n{answers_text}\n\nSmíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar og laganúmer sem standa BERORÐUM í HEIMILDUM. Ef greinarnúmer vantar, tilgreindu þá bara lagið án greinar. Svaraðu á íslensku."
        
        print(f"\nDÓMARI:")
        dómari = await call_model(c, DÓMARI[0], DÓMARI[1], "Þú ert íslenskur lögfræðidómari.", judge_prompt)
        print(f"  {dómari['model']}: {dómari['latency']:.0f}ms | svar={len(dómari['content'])} stafir")
        
        is_valid, _ = _validate_response(dómari["content"], rag_citations)
        t_total = (time.time() - t_start) * 1000
        
        print(f"\nNIÐURSTAÐA:")
        print(f"  Heildartími: {t_total:.0f}ms")
        print(f"  Grounding: {is_valid}")
        print(f"  Módel sem svöruðu: {len(ok)}/{len(PANEL)}")

asyncio.run(main())
