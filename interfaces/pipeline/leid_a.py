"""Leið A — OpenRouter chain (general tier).

Chain: Gemini 3.1 Pro Preview -> Claude Sonnet 4.6 -> DeepSeek V3 -> GPT-4o-mini
ZDR-confirmed. Sprint 68 Leið A v2.
Returns: (content, model_used, usage_dict) or (None, None, None).
"""
import logging
import os
logger = logging.getLogger("alvitur.web")


async def _call_leid_a(system_prompt, user_msg, max_tokens=1500):
    """OpenRouter chain: Haiku -> Sonnet -> gpt-4o-mini. Returns (content, model, usage)."""
    from interfaces.config import MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY, MODEL_LEIDA_A_ULTIMATE
    import httpx as _hx
    _key = os.environ.get("OPENROUTER_API_KEY", "")
    if not _key:
        logger.error("[ALVITUR] leid_a: OPENROUTER_API_KEY missing")
        return (None, None, None)
    if os.environ.get("OPENROUTER_ZDR_CONFIRMED", "false") != "true":
        logger.warning("[ALVITUR] leid_a: ZDR_CONFIRMED=false - refusing call")
        return (None, None, None)
    chain = [MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY, MODEL_LEIDA_A_ULTIMATE]
    async with _hx.AsyncClient() as c:
        for idx, model in enumerate(chain):
            try:
                r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {_key}", "HTTP-Referer": "https://alvitur.is", "X-Title": "Alvitur"},
                    json={
                        "model": model,
                        "messages": [{"role":"system","content":system_prompt},{"role":"user","content":user_msg}],
                        "max_tokens": max_tokens,
                        "reasoning": {"exclude": True},  # s68-hotfix Part 3: suppress thinking-leak
                    },
                    timeout=30.0)
                if r.status_code != 200:
                    logger.warning(f"[ALVITUR] leid_a step={idx+1}/4 model={model} status={r.status_code}")
                    continue
                d = r.json()
                logger.info(f"[ALVITUR] leid_a {'FALLBACK' if idx>0 else 'primary'} ok step={idx+1}/4 model={model}")
                return (d["choices"][0]["message"]["content"], model, d.get("usage", {}))
            except Exception as e:
                logger.warning(f"[ALVITUR] leid_a step={idx+1}/3 exc={type(e).__name__}: {e}")
    logger.error("[ALVITUR] leid_a ALL 4 models failed")
    return (None, None, None)


