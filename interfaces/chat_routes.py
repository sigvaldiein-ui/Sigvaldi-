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
from core.db_manager import skra_audit

# Sprint 61.2: Vault concurrency guard — serialize til að forðast OOM á A40 (40/46 GB)
# Max 1 samtímis vault call. General tier óbreytt (cloud handle concurrency).
import asyncio as _aio
_VAULT_SEMAPHORE = _aio.Semaphore(1)


def _get_rag_context(query: str, domain: str = None) -> str:
    """RAG+ retrieval fyrir chat_routes (sovereign-by-default)."""
    from core.rag_orchestrator import retrieve_legal_context, build_rag_injection
    rag_result = retrieve_legal_context(
        query=query,
        intent_domain=domain or 'general',
        tier='vault',
        tenant_id='system',
    )
    if rag_result.refusal:
        return '__RAG_REFUSAL__:' + rag_result.refusal
    if not rag_result.used_retrieval:
        return ''
    return build_rag_injection(rag_result.chunks)


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
                    "max_tokens": 4096,
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
    async with httpx.AsyncClient(timeout=180.0) as c:
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
                        "max_tokens": 4096,
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



from fastapi.responses import StreamingResponse
import json as _json

async def _stream_general_chain(system_prompt: str, query: str):
    """OpenRouter streaming — sendir token jafnóðum til notanda."""
    from interfaces.config import MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        yield f"data: {_json.dumps({'error': 'OPENROUTER_API_KEY missing'})}\n\n"
        return
    if os.environ.get("OPENROUTER_ZDR_CONFIRMED", "false") != "true":
        yield f"data: {_json.dumps({'error': 'ZDR_CONFIRMED=false'})}\n\n"
        return
    
    chain = [MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY]
    async with httpx.AsyncClient(timeout=180.0) as c:
        for idx, model in enumerate(chain):
            try:
                async with c.stream(
                    "POST",
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
                        "max_tokens": 4096,
                        "temperature": 0.2,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code == 200:
                        full_content = ""
                        async for line in response.aiter_lines():
                            if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                                try:
                                    data = _json.loads(line[6:])
                                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        full_content += delta
                                        yield f"data: {_json.dumps({'token': delta, 'model': model})}\n\n"
                                except Exception:
                                    pass
                        yield f"data: {_json.dumps({'done': True, 'content': full_content, 'model': model, 'tier': 'general'})}\n\n"
                        return
                    else:
                        logger.warning(f"[SSE] model={model} status={response.status_code}")
            except Exception as e:
                logger.warning(f"[SSE] model={model} exc={type(e).__name__}: {e}")
        yield f"data: {_json.dumps({'error': 'All models failed'})}\n\n"



async def _stream_openrouter(system_prompt: str, query: str):
    """OpenRouter streaming með fallback (Sprint 79.2)."""
    from interfaces.config import MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        logger.warning("[SSE] OpenRouter lykil vantar — notar local vLLM")
        return
    if os.environ.get("OPENROUTER_ZDR_CONFIRMED", "false") != "true":
        logger.warning("[SSE] ZDR_CONFIRMED=false — notar local vLLM")
        return
    
    chain = [MODEL_LEIDA_A_PRIMARY, MODEL_LEIDA_A_SECONDARY, MODEL_LEIDA_A_TERTIARY]
    async with httpx.AsyncClient(timeout=180.0) as c:
        for idx, model in enumerate(chain):
            try:
                async with c.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://alvitur.is", "X-Title": "Alvitur"},
                    json={"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"SPURNING: {query}"}], "max_tokens": 4096, "temperature": 0.2, "stream": True},
                ) as response:
                    if response.status_code == 200:
                        full_content = ""
                        async for line in response.aiter_lines():
                            if line.startswith("data: ") and not line.startswith("data: [DONE]"):
                                try:
                                    data = _json.loads(line[6:])
                                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        full_content += delta
                                        line_out = "data: " + _json.dumps({"token": delta, "model": model.split("/")[-1], "source": "openrouter"}) + "\n\n"
                                        yield line_out
                                except Exception:
                                    pass
                        line_out = "data: " + _json.dumps({"done": True, "content": full_content, "model": model, "tier": "general", "source": "openrouter"}) + "\n\n"
                        yield line_out
                        return
            except Exception as e:
                logger.warning(f"[SSE] OpenRouter {model} villa: {type(e).__name__}")
        logger.warning("[SSE] Allar OpenRouter tilraunir mistókust")



async def stream_chat(request: Request):
    """SSE streaming endapunktur — Sprint 79."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
    
    query = body.get("query", "").strip()
    if not query:
        return JSONResponse(status_code=422, content={"error_code": "empty_prompt"})
    
    tier = body.get("tier", "general").lower()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Build system prompt
    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "réttur"]) else "general"
    rag_context = _get_rag_context(query, domain)
    sys_prompt = _general_system_prompt(query, "", rag_context, now_str)
    
    return StreamingResponse(
        _stream_general_chain(sys_prompt, query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def handle_chat(request: Request, query: str, tier: str = "general", ragnum=None, attached_files: list | None = None):
    """Sprint 61 — sovereign-aware chat endpoint.
    Tier 'vault' -> local vLLM only (no cloud fallback, 503 if down).
    Tier 'general' -> OpenRouter chain Haiku -> Sonnet -> gpt-4o-mini.
    """
    files = attached_files or []
    logger.info(f"[ALVITUR] chat_routes Sprint61 tier={tier} query_len={len(query)} files={len(files)}")

    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "réttur", "persónuvernd", "gagnavernd"]) else "general"
    if ragnum and ragnum.chunks:
        rag = "\n\n".join(c.get("text","")[:500] for c in ragnum.chunks[:3])
    else:
        rag = _get_rag_context(query, domain)

    # Sprint 70 D.5 — sovereign refusal (gildir fyrir bada tier-ar i chat_routes)
    if rag.startswith("__RAG_REFUSAL__:"):
        refusal_msg = rag.replace("__RAG_REFUSAL__:", "")
        return JSONResponse({
            "answer": refusal_msg,
            "tier": tier,
            "pipeline_source": f"rag_refusal_{tier}",
            "rag_metadata": {
                "used_retrieval": True,
                "tier": tier,
                "chunks_count": 0,
                "top_score": 0.0,
                "source_laws": [],
                "low_confidence": False,
            }
        })
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
        # Sprint 61.2: semaphore til að forðast OOM
        async with _VAULT_SEMAPHORE:
            logger.info(f"[VAULT] semaphore acquired, processing vault call")
            content, model, usage = await _call_vault_local(query, sys_prompt)
        logger.info(f"[VAULT] semaphore released")
        if content is None:
            return JSONResponse(status_code=503, content={
                "success": False,
                "error_code": "vault_local_unavailable",
                "detail": "Trúnaðarþjónusta tímabundið ekki tiltæk. Local AI module er að ræsast — reyndu aftur eftir 1 mínútu.",
            })
        skra_audit(action="CHAT_QUERY", tier=tier, query_text=query, success=True)
        return JSONResponse(content={
            "success": True,
            "response": content,
            "pipeline_source": f"rag_grounded_vault" if rag else f"local_vllm_{model}",
            "domain": domain,
            "tier": "vault",
        })

    # ── Leið A: General OpenRouter chain ─────────────────────────────
    # 🟢 Sprint 62 Patch G: sovereign fallback ef Leið A mistekst eða key vantar
    sys_prompt = _general_system_prompt(query, file_context, rag, now_str)
    _key_check = os.environ.get("OPENROUTER_API_KEY", "")
    content, model, usage = (None, None, {})
    if _key_check:
        content, model, usage = await _call_general_chain(sys_prompt, query)
    if content is None:
        logger.warning("[ALVITUR] Sprint62G chat: Leið A down/no-key → sovereign Leið B")
        try:
            vault_prompt = _vault_system_prompt_chat(query, file_context, rag, now_str)
            async with _VAULT_SEMAPHORE:
                content, model, usage = await _call_vault_local(query, vault_prompt)
        except Exception as _fe:
            logger.error(f"[ALVITUR] Sprint62G exc: {type(_fe).__name__}: {_fe}")
            content = None
        if content is None:
            return JSONResponse(status_code=503, content={
                "success": False,
                "error_code": "both_pipelines_unavailable",
                "detail": "Þjónusta tímabundið ekki aðgengileg. Reyndu eftir augnablik.",
            })
        logger.info(f"[ALVITUR] Sprint62G sovereign OK model={model}")
        skra_audit(action="CHAT_QUERY", tier=tier, query_text=query, success=True)
        return JSONResponse(content={
            "success": True,
            "response": content,
            "pipeline_source": f"sovereign_nokey_{model}",
            "domain": domain,
            "tier": "general_fallback",
        })
        skra_audit(action="CHAT_QUERY", tier=tier, query_text=query, success=True)
    return JSONResponse(content={
        "success": True,
        "response": content,
        "pipeline_source": f"openrouter_{model.split('/')[-1]}",
        "domain": domain,
        "tier": "general",
    })
