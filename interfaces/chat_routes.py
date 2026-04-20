"""
Sprint 61 — chat_routes.py með sovereign separation.
Leid A (general): OpenRouter chain Haiku -> Sonnet -> gpt-4o-mini
Leid B (vault):   LOCAL vLLM (qwen3-32b-awq) ONLY — NO cloud fallback
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import os, httpx, logging
from datetime import datetime, timezone

logger = logging.getLogger("alvitur.web")


def _get_rag_context(query: str, domain: str) -> str:
    if domain != "legal":
        return ""
    keywords = ["persónuvernd", "gagnavernd", "lög", "réttur", "heimild", "lag", "samþykki"]
    if any(kw in query.lower() for kw in keywords):
        return """
[Heimildir]
• Persónuverndarlög nr. 90/2018, 15. gr.: Réttur aðila til upplýsinga um meðferð persónuupplýsinga.
• Upplýsingalög nr. 142/2012: Almennur aðgangur að opinberum gögnum.
"""
    return ""


def _estimate_tokens(text: str) -> int:
    return int(len((text or "").split()) * 1.3)


def _vault_system_prompt_chat(query: str, file_context: str, rag: str, now_str: str) -> str:
    return (
        f"Þú ert Alvitur — íslensk gervigreindaraðstoð á trúnaðarstigi (Vault).\n"
        f"Þú keyrir á íslenskri GPU. Gögn fara aldrei úr vélinni.\n"
        f"Dagsetning: {now_str}\n{rag}{file_context}\n\n"
        f"REGLUR UM ÍSLENSKU:\n"
        f"1. Svaraðu ALLTAF á réttri íslensku með beygingum.\n"
        f"2. Gættu að föllum og kynjum.\n"
        f"3. Ekki búa til orð — umorðaðu ef óvisst.\n\n"
        f"SPURNING NOTANDANS: {query}\n"
        f"Svaraðu beint, stutt og faglega á íslensku."
    )


def _general_system_prompt(query: str, file_context: str, rag: str, now_str: str) -> str:
    return (
        f"Þú ert Alvitur, íslenskur sérfræðingur.\n"
        f"Dagsetning: {now_str}\n{rag}{file_context}\n\n"
        f"MIKILVÆGAST:\n"
        f"1. SPURNING NOTANDANS ER: \"{query}\"\n"
        f"2. Svaraðu BEINT þessari spurningu á íslensku.\n"
        f"3. Ef skrár eru meðfylgjandi, notaðu þær AÐEINS til að svara — ekki lýsa þeim.\n"
        f"4. Stutt, skýrt, faglegt svar."
    )


async def _call_vault_local(query: str, system_prompt: str):
    """Local vLLM sovereign call. Returns (content, model, usage) or (None, None, None)."""
    from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT
    try:
        async with httpx.AsyncClient(timeout=float(VAULT_LOCAL_TIMEOUT)) as c:
            r = await c.post(
                VAULT_LOCAL_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "model": VAULT_LOCAL_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 600,
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
            if r.status_code != 200:
                logger.error(f"[ALVITUR] chat_routes vault vLLM status={r.status_code} body={r.text[:200]}")
                return (None, None, None)
            d = r.json()
            ms = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
            u = d.get("usage", {})
            logger.info(f"[ALVITUR] chat_routes leid_b sovereign ok model={ms} in={u.get('prompt_tokens',0)} out={u.get('completion_tokens',0)}")
            return (d["choices"][0]["message"]["content"].strip(), ms, u)
    except Exception as e:
        logger.error(f"[ALVITUR] chat_routes vault exc: {type(e).__name__}: {e}")
        return (None, None, None)


async def _call_general_chain(system_prompt: str, query: str):
    """OpenRouter chain Haiku -> Sonnet -> gpt-4o-mini. Returns (content, model, usage) or (None, None, None)."""
    from interfaces.config import (
        MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY)
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        logger.error("[ALVITUR] chat_routes leid_a: OPENROUTER_API_KEY missing")
        return (None, None, None)
    if os.environ.get("OPENROUTER_ZDR_CONFIRMED", "false") != "true":
        logger.warning("[ALVITUR] chat_routes leid_a: ZDR_CONFIRMED=false - refusing")
        return (None, None, None)
    chain = [MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY]
    async with httpx.AsyncClient(timeout=60.0) as c:
        for idx, model in enumerate(chain):
            try:
                r = await c.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "HTTP-Referer": "https://alvitur.is",
                        "X-Title": "Alvitur",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"SPURNING: {query}"},
                        ],
                        "max_tokens": 600,
                        "temperature": 0.2,
                    },
                )
                if r.status_code != 200:
                    logger.warning(f"[ALVITUR] chat_routes leid_a step={idx+1}/3 model={model} status={r.status_code}")
                    continue
                d = r.json()
                logger.info(f"[ALVITUR] chat_routes leid_a {'FALLBACK' if idx>0 else 'primary'} ok step={idx+1}/3 model={model}")
                return (d["choices"][0]["message"]["content"].strip(), model, d.get("usage", {}))
            except Exception as e:
                logger.warning(f"[ALVITUR] chat_routes leid_a step={idx+1}/3 exc: {type(e).__name__}: {e}")
    logger.error("[ALVITUR] chat_routes leid_a ALL 3 models failed")
    return (None, None, None)


async def handle_chat(request: Request, query: str, tier: str = "general", attached_files: list | None = None):
    """Sprint 61 — sovereign-aware chat endpoint.
    Tier 'vault' -> local vLLM only (no cloud fallback, 503 if down).
    Tier 'general' -> OpenRouter chain Haiku -> Sonnet -> gpt-4o-mini.
    """
    files = attached_files or []
    logger.info(f"[ALVITUR] chat_routes Sprint61 tier={tier} query_len={len(query)} files={len(files)}")

    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "réttur", "persónuvernd", "gagnavernd"]) else "general"
    rag = _get_rag_context(query, domain)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    file_context = ""
    if files:
        file_context = "\n\n[MEÐFYLGJANDI SKJÖL]:"
        for i, f in enumerate(files[:3], 1):
            fname = f.get("filename", f"Skjal {i}")
            content = f.get("content", "")[:1500]
            file_context += f"\n--- {fname} ---\n{content}"
        file_context += "\n[ENDIR SKJALA]"

    # ── Leið B: Vault sovereign ──────────────────────────────────────
    if tier == "vault":
        from interfaces.config import VAULT_MAX_INPUT_TOKENS
        total_text = query + file_context
        if _estimate_tokens(total_text) > VAULT_MAX_INPUT_TOKENS:
            return JSONResponse(status_code=413, content={
                "success": False,
                "error_code": "vault_input_too_large",
                "detail": f"Fyrirspurn er of stór fyrir Vault tier (max {VAULT_MAX_INPUT_TOKENS} tokens). Styttu textann eða skiptu í hluta.",
            })
        sys_prompt = _vault_system_prompt_chat(query, file_context, rag, now_str)
        content, model, usage = await _call_vault_local(query, sys_prompt)
        if content is None:
            return JSONResponse(status_code=503, content={
                "success": False,
                "error_code": "vault_local_unavailable",
                "detail": "Trúnaðarþjónusta tímabundið ekki tiltæk. Local AI module er að ræsast — reyndu aftur eftir 1 mínútu.",
            })
        return JSONResponse(content={
            "success": True,
            "response": content,
            "pipeline_source": f"local_vllm_{model}",
            "domain": domain,
            "tier": "vault",
        })

    # ── Leið A: General OpenRouter chain ─────────────────────────────
    sys_prompt = _general_system_prompt(query, file_context, rag, now_str)
    content, model, usage = await _call_general_chain(sys_prompt, query)
    if content is None:
        return JSONResponse(status_code=502, content={
            "success": False,
            "error_code": "llm_unavailable",
            "detail": "Ekki tókst að ná sambandi við greiningar þjónustu. Reyndu aftur.",
        })
    return JSONResponse(content={
        "success": True,
        "response": content,
        "pipeline_source": f"openrouter_{model.split('/')[-1]}",
        "domain": domain,
        "tier": "general",
    })
