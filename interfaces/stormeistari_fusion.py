"""Stórmeistari Fusion — Nebius panel með dómara gegnum LiteLLM gátt."""
import httpx, asyncio, logging, re, time

logger = logging.getLogger("alvitur.stormeistari")

GATT_URL = "http://127.0.0.1:4000/v1/chat/completions"
GATT_KEY = "alvitur-gatt-2026"

PANEL = {
    "GLM-5.2": "nebius-glm",
    "Qwen3-235B": "nebius-qwen",
    "DeepSeek-V4-Pro": "nebius-deepseek",
    "GPT-OSS-120B": "nebius-gpt-oss",
}
JUDGE_MODEL = "nebius-gpt-oss"


async def _call_one(client, model_id, system_prompt, user_msg, max_tok):
    try:
        r = await client.post(GATT_URL,
            headers={"Authorization": f"Bearer {GATT_KEY}"},
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": max_tok if "glm" not in model_id.lower() else 2000,
                "temperature": 0.1,
            }, timeout=120)
        d = r.json()
        return d["choices"][0]["message"]["content"] if "choices" in d else None
    except Exception as e:
        logger.warning(f"[Stórmeistari] Panel {model_id} villa: {e}")
        return None


async def _call_nebius_fusion(system_prompt, user_msg, max_tokens=1500):
    """Keyrir 4-módela panel + dómara í gegnum LiteLLM gátt."""
    async with httpx.AsyncClient(timeout=180) as client:
        tasks = [
            _call_one(client, mid, system_prompt, user_msg, max_tokens)
            for mid in PANEL.values()
        ]
        results = await asyncio.gather(*tasks)
        ok = [r for r in results if r]
        if len(ok) < 2:
            logger.warning(f"[Stórmeistari] Aðeins {len(ok)} módel svöruðu")
            return None, None, None

        answers = "\n\n".join([f"Svar {i+1}:\n{r}" for i, r in enumerate(ok)])
        judge_prompt = f"{system_prompt}\n\n{user_msg}\n\n{answers}\n\nSmíðaðu eitt sameinað svar úr þessum svörum."

        try:
            r = await client.post(GATT_URL,
                headers={"Authorization": f"Bearer {GATT_KEY}"},
                json={
                    "model": JUDGE_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": judge_prompt}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.1,
                }, timeout=120)
            d = r.json()
            content = d["choices"][0]["message"]["content"] if "choices" in d else None
            usage = d.get("usage", {})
            return content, f"Gatt-{JUDGE_MODEL}", usage
        except Exception as e:
            logger.warning(f"[Stórmeistari] Dómari villa: {e}")
            return None, None, None


async def run_stormeistari(query, search_text, citations, hvelfingin_search, web_search, t_start):
    """Inngangsfall fyrir Stórmeistara. Skilar dict eða None."""
    if hvelfingin_search:
        return None

    try:
        from core.safety.pii_sentry import scrub as pii_scrub
        from interfaces.chat_routes import _validate_response

        safe_result = pii_scrub(query)
        safe_query = safe_result.scrubbed
        safe_result = pii_scrub(search_text)
        safe_context = safe_result.scrubbed

        system_prompt = (
            "Þú ert Alvitur — íslensk gervigreindarlausn. "
            "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
            "Tilgreindu alltaf heimildir.\n\n"
            f"HEIMILDIR:\n{safe_context}\n\n"
            "Svaraðu á íslensku."
        )
        user_msg = f"Spurning: {query}"

        content, model, usage = await _call_nebius_fusion(system_prompt, user_msg)

        if not content:
            return None

        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        is_valid, guarded = _validate_response(cleaned, citations)
        if not is_valid:
            cleaned = guarded

        return {
            "success": True,
            "response": cleaned,
            "citations": citations,
            "sources": {
                "sovereign": True,
                "web_search": web_search,
                "stormeistari": True,
            },
            "pipeline": "nebius_fusion",
            "tier": "vitinn",
            "confidence": 0.9,
            "latency_ms": (time.time() - t_start) * 1000,
        }
    except Exception as e:
        logger.warning(f"[Stórmeistari] Fellur til baka: {e}")
        return None
