"""Fusion Service — Stórmeistari panel + dómari."""
import httpx, json, os, logging, asyncio

logger = logging.getLogger("alvitur.fusion")

FUSION_PANEL = [
    ("deepseek/deepseek-chat", "DeepSeek"),
    ("z-ai/glm-5.2", "GLM-5.2"),
    ("moonshotai/kimi-k2.6", "Kimi K2.6"),
]
FUSION_JUDGE = "deepseek/deepseek-chat"

async def _call_model(client, model, name, system_prompt, user_msg, or_key, max_tokens=300):
    """Kallar á eitt módel í Fusion-panelinu."""
    try:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": max_tokens,
            },
            timeout=60.0,
        )
        d = r.json()
        if 'choices' in d:
            return {
                "ok": True,
                "answer": d['choices'][0]['message']['content'],
                "model": model,
                "name": name,
                "cost": d.get('usage', {}).get('cost', 0),
            }
        else:
            logger.warning(f"[Fusion] {name} villa: {json.dumps(d)[:200]}")
            return {"ok": False, "model": model, "name": name, "error": str(d)[:200]}
    except Exception as e:
        logger.warning(f"[Fusion] {name} exception: {e}")
        return {"ok": False, "model": model, "name": name, "error": str(e)[:200]}

async def run_fusion(query: str, rag_context: str, rag_citations: list, quality: str = "brons") -> dict | None:
    """Keyrir Fusion-panel + dómara. Skilar dict eða None ef allt fellur."""
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not or_key:
        logger.warning("[Fusion] Enginn OpenRouter lykill")
        return None

    system_prompt = (
        "Þú ert Alvitur — íslensk gervigreindarlausn. "
        "Svaraðu eftirfarandi spurningu byggt á meðfylgjandi heimildum. "
        "Tilgreindu alltaf heimildir.\n\n"
        f"HEIMILDIR:\n{rag_context}\n\n"
        "Svaraðu á íslensku."
    )
    user_msg = f"Spurning: {query}"

    async with httpx.AsyncClient(timeout=90.0) as client:
        # Fan-out — kalla á öll panel-módel samtímis
        tasks = [_call_model(client, m, n, system_prompt, user_msg, or_key) for m, n in FUSION_PANEL]
        results = await asyncio.gather(*tasks)

        ok_results = [r for r in results if r["ok"]]
        if len(ok_results) < 2:
            logger.warning(f"[Fusion] Aðeins {len(ok_results)}/{len(FUSION_PANEL)} módel svöruðu — fell")
            return None

        # Dómari — smíðar sameinað svar
        answers_text = "\n\n".join([f"Svar {i+1} ({r['name']}):\n{r['answer']}" for i, r in enumerate(ok_results)])
        judge_prompt = f"""Spurning: {query}

HEIMILDIR:
{rag_context}

{answers_text}

Smíðaðu EITT sameinað svar byggt á þessum svörum og HEIMILDUNUM. Vitnaðu eingöngu í greinar sem eru í HEIMILDUM. Svaraðu á íslensku."""

        try:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                json={
                    "model": FUSION_JUDGE,
                    "messages": [{"role": "user", "content": judge_prompt}],
                    "max_tokens": 500,
                },
                timeout=60.0,
            )
            d = r.json()
            if 'choices' in d:
                merged = d['choices'][0]['message']['content']
                total_cost = sum(r["cost"] for r in ok_results) + d.get('usage', {}).get('cost', 0)
                logger.info(f"[Fusion] Tókst — {len(ok_results)}/{len(FUSION_PANEL)} módel, kostnaður ${total_cost:.4f}")
                return {
                    "answer": merged,
                    "models": [r["name"] for r in ok_results],
                    "cost": total_cost,
                    "pipeline": f"fusion_{'+'.join([r['name'].replace(' ','-') for r in ok_results])}",
                }
            else:
                logger.warning(f"[Fusion] Dómari villa: {json.dumps(d)[:200]}")
                return None
        except Exception as e:
            logger.warning(f"[Fusion] Dómari exception: {e}")
            return None
