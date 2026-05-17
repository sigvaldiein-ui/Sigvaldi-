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
from core.agents.yfir_erindreki import yfir_erindreki
from core.agent_core_v5 import AgentResult

logger = logging.getLogger("alvitur.web")

# Sprint 82: Audit trail logging
def _audit_log(timestamp: str, tier: str, query: str, intent: str,
               search_context_len: int, citations_count: int,
               pipeline_source: str, response_len: int, response_time_ms: float, user_id: str = "anonymous"):
    import os
    audit_dir = os.path.join(os.path.dirname(__file__), '..', 'audit')
    os.makedirs(audit_dir, exist_ok=True)
    log_file = os.path.join(audit_dir, f"{timestamp[:10]}.jsonl")
    entry = {
        "timestamp": timestamp,
        "user_id": user_id,
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

async def _get_rag_context(query: str, domain: str) -> dict:
    """Sækir lagalegt samhengi úr Qdrant í gegnum SearchLawTool og skilar DICT."""
    if domain != "legal":
        return {"text": "", "citations": []}
    
    try:
        from interfaces.tools.search_law import SearchLawTool
        tool = SearchLawTool()
        hits = await tool.run(query)
        if hits:
            lines = ["[Heimildir — íslensk lög og reglugerðir]"]
            citations = []
            for h in hits:
                lines.append(f"• {h.get('title', '')}: {h.get('text', '')[:300]}")
                citations.append({
                    "url": h.get("source", ""),
                    "title": h.get("title", ""),
                    "snippet": h.get("text", "")[:200]
                })
            return {"text": "\n".join(lines), "citations": citations}
    except Exception as e:
        import sys
        print(f"RAG villa: {e}", file=sys.stderr)
    
    return {"text": "", "citations": []}

def _strip_pii_for_search(query: str) -> tuple:
    KT_PATTERN = r'\b\d{6}-?\d{4}\b'
    sanitized = re.sub(KT_PATTERN, '[KT]', query)
    had_pii = sanitized != query
    return sanitized, had_pii

async def _get_search_context(query: str, domain: str) -> dict:
    """Sprint 80c: Skilar alltaf {'text': str, 'citations': list}."""
    logger.info(f"[80c] _get_search_context query={query[:50]}")
    
    # 1. RAG Check
    rag_result = await _get_rag_context(query, domain)
    if rag_result.get("text"):
        return rag_result

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
    
    async with httpx.AsyncClient(timeout=300.0) as c:
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
    audit_user_id = "anonymous"
    try:
        from interfaces.middleware.auth import get_current_user
        cu = get_current_user(request)
        if cu: audit_user_id = str(cu.get("user_id", "anonymous"))
    except: pass
    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "laga", "laganna", "réttur", "rétt", "persónuvernd", "personuvernd", "reglugerð", "reglugerd", "stjórnsýsla", "stjornsysla", "alþingi", "althingi", "gr.", "grein", "þingsályktun", "thingsalyktun", "skipulag", "dómur", "domur", "úrskurður", "urskurdur"]) else "general"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    files = attached_files or []
    file_context = ""
    if files:
        file_context = "\n[SKJÖL]:" + "".join([f"\n- {f.get('filename')}: {f.get('content','')[:1000]}" for f in files[:3]])
    
    # ── SPRINT 83: YfirErindreki (Orchestrator) ─────────────────
    # Allar fyrirspurnir fara í gegnum YfirErindreka sem:
    # 1. Greinir PII (PII Sentry)
    # 2. Athugar skyndiminni (Semantic Cache)
    # 3. Metur flækjustig (Complexity Score)
    # 4. Velur réttan agent
    # 5. Framkvæmir með Circuit Breaker vernd
    
    # Undirbúa context fyrir orchestrator
    search_res = await _get_search_context(query, domain)
    import sys; sys.stderr.write(f"DEBUG search_res: text_len={len(search_res.get('text', ''))}, citations_len={len(search_res.get('citations', []))}\n")
    final_citations = search_res["citations"]
    
    orchestrator_context = {
        "search_text": search_res["text"],
        "citations": final_citations,
        "file_context": file_context,
        "domain": domain,
    }
    
    # Kalla á YfirErindreka
    result = await yfir_erindreki.handle(query, tier, attached_files, orchestrator_context)
    
    # Ef orchestrator skilar villu
    if result.response is None or result.confidence == 0.0:
        _audit_log(now_str, tier, query, domain, len(search_res.get("text", "")),
                   len(final_citations), "orchestrator_error", 0,
                   (time.time() - start_time) * 1000, audit_user_id)
        return JSONResponse(status_code=503, content={
            "success": False,
            "detail": result.response or "Þjónusta tímabundið ekki aðgengileg."
        })
    
    # Skrá í audit trail
    _audit_log(now_str, result.tier, query, domain, len(search_res.get("text", "")),
               len(final_citations), f"{result.agent_name}_{result.model_used}",
               len(result.response or ""),
               (time.time() - start_time) * 1000, audit_user_id)
    
    # Skila svari
    return JSONResponse(content={
        "success": True,
        "response": result.response,
        "citations": final_citations,
        "pipeline_source": f"{result.agent_name}_{result.model_used}",
        "tier": result.tier,
        "confidence": result.confidence,
        "cost_usd": result.cost_usd,
    })
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    files = attached_files or []
    file_context = ""
    if files:
        file_context = "\n[SKJÖL]:" + "".join([f"\n- {f.get('filename')}: {f.get('content','')[:1000]}" for f in files[:3]])

