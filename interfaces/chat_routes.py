"""
Sprint 61 — chat_routes.py með sovereign separation og öruggum citations.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import json
import os, httpx, logging, re
from datetime import datetime, timezone
import time
from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT

logger = logging.getLogger("alvitur.web")

# Sprint 82: Audit trail logging
def _audit_log(timestamp: str, tier: str, query: str, intent: str,
               search_context_len: int, citations_count: int,
               pipeline_source: str, response_len: int, response_time_ms: float):
    import os
    audit_dir = os.path.join(os.path.dirname(__file__), '..', 'audit')
    os.makedirs(audit_dir, exist_ok=True)
    log_file = os.path.join(audit_dir, f"{timestamp[:10]}.jsonl")
    entry = {
        "timestamp": timestamp,
        "tier": tier,
        "query": query[:100],
        "intent": intent,
        "search_context_len": search_context_len,
        "citations_count": citations_count,
        "pipeline_source": pipeline_source,
        "response_len": response_len,
        "response_time_ms": round(response_time_ms, 2),
    }
    import json
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

import asyncio as _aio
_VAULT_SEMAPHORE = _aio.Semaphore(1)

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

def _strip_pii_for_search(query: str) -> tuple:
    KT_PATTERN = r'\b\d{6}-?\d{4}\b'
    sanitized = re.sub(KT_PATTERN, '[KT]', query)
    had_pii = sanitized != query
    return sanitized, had_pii

async def _get_search_context(query: str, domain: str) -> dict:
    """Sprint 80c: Skilar alltaf {'text': str, 'citations': list}."""
    logger.info(f"[80c] _get_search_context query={query[:50]}")
    
    # 1. RAG Check
    rag = _get_rag_context(query, domain)
    if rag:
        return {"text": rag, "citations": []}

    # 2. Web Search
    try:
        from tools.search_web_multi import search_web_multi
        res = await search_web_multi(query, max_results=6)
        citations = res.get("citations", [])
        
        if not citations:
            return {"text": "", "citations": []}

        lines = ["[Vefleit - Mojeek]"]
        for c in citations:
            title = c.get("title", "Heimild")
            url = c.get("url", "")
            snippet = c.get("snippet", "")
            lines.append(f"* {title}: {url}")
            if snippet:
                lines.append(f"  {snippet}")
        
        return {
            "text": "\n".join(lines),
            "citations": citations
        }
    except Exception as e:
        logger.error(f"[80c] Web search failed: {e}")
        return {"text": "", "citations": []}

def _estimate_tokens(text: str) -> int:
    return int(len((text or "").split()) * 1.3)

def _vault_system_prompt_chat(query: str, file_context: str, rag: str, now_str: str) -> str:
    return (
        f"Thu ert Alvitur. Dagsetning: {now_str}.\n\n"
        f"HEIMILD-GOGN:\n{rag}{file_context}\n"
        "REGLUR: 1. Heimildir hafa forgang. 2. Stutt svar.\n"
        f"SPURNING: {query}"
    )

def _general_system_prompt(query: str, file_context: str, rag: str, now_str: str) -> str:
    return (
        f"Þú ert Alvitur, íslenskur sérfræðingur. Dagsetning: {now_str}\n\n"
        f"=== HEIMILDIR ===\n{rag}{file_context}\n"
        f"MIKILVÆGT: Notaðu heimildir fyrst. Svaraðu á íslensku.\n"
        f"SPURNING: {query}"
    )

async def _call_vault_local(query: str, system_prompt: str):
    try:
        async with httpx.AsyncClient(timeout=float(VAULT_LOCAL_TIMEOUT)) as c:
            r = await c.post(
                VAULT_LOCAL_URL,
                json={
                    "model": VAULT_LOCAL_MODEL,
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                    "max_tokens": 4096, "temperature": 0.3
                },
            )
            if r.status_code != 200: return (None, None, None)
            d = r.json()
            return (d["choices"][0]["message"]["content"].strip(), VAULT_LOCAL_MODEL, d.get("usage", {}))
    except Exception as e:
        logger.error(f"Vault error: {e}")
        return (None, None, None)

async def _call_general_chain(system_prompt: str, query: str):
    from interfaces.config import MODEL_LEIDA_A_PRIMARY as m_p
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key or os.environ.get("OPENROUTER_ZDR_CONFIRMED") != "true": return (None, None, None)
    
    async with httpx.AsyncClient(timeout=180.0) as c:
        try:
            r = await c.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "X-Title": "Alvitur"},
                json={"model": m_p, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}], "temperature": 0.2},
            )
            if r.status_code == 200:
                d = r.json()
                return (d["choices"][0]["message"]["content"].strip(), m_p, d.get("usage", {}))
        except Exception as e:
            logger.error(f"General chain error: {e}")
    return (None, None, None)

async def handle_chat(request: Request, query: str, tier: str = "general", attached_files: list | None = None):
    start_time = time.time()
    # FRUMSTILLING - Tryggja að citations séu alltaf til
    final_citations = []
    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "réttur", "persónuvernd"]) else "general"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    files = attached_files or []
    file_context = ""
    if files:
        file_context = "\n[SKJÖL]:" + "".join([f"\n- {f.get('filename')}: {f.get('content','')[:1000]}" for f in files[:3]])

    # LEIÐ B: VAULT
    if tier == "vault":
        search_res = {"text": "", "citations": []}
        _search_query, _had_pii = _strip_pii_for_search(query)
        _strict = os.environ.get("VAULT_STRICT_NO_EXTERNAL", "true").lower() == "true"
        
        if not (_had_pii and _strict):
            search_res = await _get_search_context(_search_query, domain)
        
        final_citations = search_res["citations"]
        sys_prompt = _vault_system_prompt_chat(query, file_context, search_res["text"], now_str)
        
        async with _VAULT_SEMAPHORE:
            content, model, usage = await _call_vault_local(query, sys_prompt)
            
        if content is None:
            return JSONResponse(status_code=503, content={"success": False, "detail": "Vault busy/offline"})

        _audit_log(now_str, "vault", query, domain, len(search_res.get("text", "")),
                   len(final_citations), f"local_{model}", len(content or ""),
                   (time.time() - start_time) * 1000)
        return JSONResponse(content={
            "success": True, "response": content, "citations": final_citations,
            "pipeline_source": f"local_{model}", "tier": "vault"
        })

    # LEIÐ A: GENERAL
    search_res = await _get_search_context(query, domain)
    final_citations = search_res["citations"]
    sys_prompt = _general_system_prompt(query, file_context, search_res["text"], now_str)
    
    content, model, usage = await _call_general_chain(sys_prompt, query)
    
    if content is None: # Fallback ef OpenRouter klikkar
        async with _VAULT_SEMAPHORE:
            content, model, usage = await _call_vault_local(query, sys_prompt)
    
    if content is None:
        _audit_log(now_str, tier, query, domain, len(search_res.get("text", "")),
               len(final_citations), "none", 0, (time.time() - start_time) * 1000)
        return JSONResponse(status_code=503, content={"success": False, "detail": "All pipelines down"})

    _audit_log(now_str, "general", query, domain, len(search_res.get("text", "")),
               len(final_citations), str(model), len(content or ""),
               (time.time() - start_time) * 1000)
    return JSONResponse(content={
        "success": True, "response": content, "citations": final_citations,
        "pipeline_source": model, "tier": "general"
    })
