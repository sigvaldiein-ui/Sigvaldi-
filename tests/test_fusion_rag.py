import os, httpx, json, asyncio, time, sys

key = os.environ["NEBIUS_API_KEY"]
base = "https://api.tokenfactory.nebius.com/v1"
sys.path.insert(0, "/workspace/Sigvaldi-")

PANEL = {
    "GLM-5.2": ("zai-org/GLM-5.2", 4000),
    "Qwen3-235B": ("Qwen/Qwen3-235B-A22B-Instruct-2507", 500),
    "DeepSeek-V4-Pro": ("deepseek-ai/DeepSeek-V4-Pro", 500),
    "GPT-OSS-120B": ("openai/gpt-oss-120b", 500),
}
DÓMARI = ("openai/gpt-oss-120b", 1000)

async def call_model(client, model_id, max_tok, system_prompt, user_msg):
    t0 = time.time()
    r = await client.post(f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": max_tok,
            "temperature": 0.1,
        }, timeout=180)
    t1 = time.time()
    d = r.json()
    content = ""
    if "choices" in d:
        content = d['choices'][0]['message'].get('content') or ""
    usage = d.get("usage", {})
    return {
        "model": model_id,
        "status": r.status_code,
        "latency": (t1-t0)*1000,
        "content": content,
        "in_tok": usage.get("prompt_tokens", 0),
        "out_tok": usage.get("completion_tokens", 0),
    }

def validate_grounding(text, citations):
    try:
        from interfaces.chat_routes import _validate_response
        is_valid, guarded = _validate_response(text, citations)
        return is_valid, guarded
    except Exception as e:
        print(f"[Vörður] Villa: {e}")
        return True, text

async def main():
    query = "Hvað segja íslensk lög um veikindarétt?"
    print("="*60)
    print(f"SPURNING: {query}")
    print("="*60)

    # RAG með réttri embedding-leit
    from interfaces.chat_routes import _get_rag_context
    rag = await _get_rag_context(query, "legal")
    rag_text = rag.get("text", "")
    rag_citations = rag.get("citations", [])
    print(f"\n[RAG] Texti: {len(rag_text)} stafir, Heimildir: {len(rag_citations)}")
    print(f"Fyrsta heimild: {rag_citations[0]['title'] if rag_citations else 'enga'}")
    print(f"RAG texti (fyrstu 400):\n{rag_text[:400]}\n")

    system_prompt = (
        "Þú ert Alvitur — íslensk gervigreindarlausn. "
        "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
        "Tilgreindu alltaf heimildir.\n\n"
        f"HEIMILDIR:\n{rag_text}\n\n"
        "Svaraðu á íslensku."
    )
    user_msg = f"Spurning: {query}"

    async with httpx.AsyncClient(timeout=180) as c:
        # Fan-out: Panel
        print("="*60)
        print("FUSION PANEL — Fan-out")
        print("="*60)
        tasks = [call_model(c, mid, mtok, system_prompt, user_msg) for mid, mtok in PANEL.values()]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(f"\n--- {r['model']} ---")
            print(f"  Status: {r['status']} | {r['latency']:.0f}ms | in={r['in_tok']} out={r['out_tok']}")
            print(f"  {r['content'][:400]}")

        ok = [r for r in results if r["content"]]
        if len(ok) < 2:
            print("\n[DÓMARI] Of fá svör — hætti")
            return

        # Dómari
        answers_text = "\n\n".join([f"Svar {i+1} ({r['model']}):\n{r['content']}" for i, r in enumerate(ok)])
        judge_prompt = (
            f"HEIMILDIR:\n{rag_text}\n\n"
            f"Spurning: {query}\n\n"
            f"{answers_text}\n\n"
            "Smíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar úr HEIMILDUM. Svaraðu á íslensku."
        )
        print("\n" + "="*60)
        print("DÓMARI")
        print("="*60)
        dómari = await call_model(c, DÓMARI[0], DÓMARI[1],
            "Þú ert íslenskur lögfræðidómari.",
            judge_prompt)
        print(f"  Status: {dómari['status']} | {dómari['latency']:.0f}ms")
        print(f"  Dómari svar:\n{dómari['content'][:800]}")

        # Grounding-vörður
        print("\n" + "="*60)
        print("GROUNDING-VÖRÐUR")
        print("="*60)
        is_valid, guarded = validate_grounding(dómari["content"], rag_citations)
        print(f"  grounding_ok: {is_valid}")
        if not is_valid:
            print(f"  Varað svar: {guarded[:500]}")

        print("\n" + "="*60)
        print("LOKASKREF: Senda hrá gögn til Opus")
        print("="*60)

asyncio.run(main())
