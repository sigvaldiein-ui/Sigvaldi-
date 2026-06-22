import re
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
def _audit_log(timestamp: str, tier: str, query: str, domain: str,
               search_context_len: int, citations_count: int,
               pipeline_source: str, response_len: int, response_time_ms: float,
               user_id: str = "anonymous", result: any = None, context: dict = None):
    """
    SOP v4.2 / Lesson #112 Compliant Audit Logger.
    Hnífskörp þrískipting gagna: actions_logged, observations_logged, final_response.
    """
    import os, json
    audit_dir = os.path.join(os.path.dirname(__file__), '..', 'audit')
    os.makedirs(audit_dir, exist_ok=True)
    log_file = os.path.join(audit_dir, f"{timestamp[:10]}.jsonl")
    
    # 1. ACTIONS LOGGED: Innri hugsanir (Inference Narrative)
    actions_logged = ""
    if result is not None:
        metadata = getattr(result, "metadata", {}) if hasattr(result, "metadata") else {}
        actions_logged = metadata.get("actions_logged", "")
    
    # 2. OBSERVATIONS LOGGED: Empirical gögn
    observations_logged = {
        "search_text": context.get("search_text", "") if context else "",
        "file_context": context.get("file_context", "") if context else "",
        "citations": getattr(result, "citations", []) if hasattr(result, "citations") else []
    }
    
    # 3. FINAL RESPONSE: Hreint svar til notanda
    final_response = getattr(result, "response", "") if hasattr(result, "response") else ""
    
    entry = {
        "timestamp": timestamp,
        "user_id": user_id,
        "tier": tier,
        "query": query[:200],
        "domain": domain,
        "actions_logged": actions_logged,
        "observations_logged": observations_logged,
        "final_response": final_response[:500],
        "search_context_len": search_context_len,
        "citations_count": citations_count,
        "pipeline_source": pipeline_source,
        "response_len": response_len,
        "response_time_ms": round(response_time_ms, 2),
    }
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


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
    """Sprint 87 Phase E: tier-first/source-first context með Hagstofu forgangi fyrir hag- og mannfjöldagögn."""
    logger.info(f"[87E] _get_search_context query={query[:50]}")
    
    q = (query or "").lower()
    hagstofa_keywords = [
        "íbúafjöldi", "ibúafjöldi", "ibúar", "íbúar", "mannfjöldi", "mannfjoldi",
        "fólksfjöldi", "population", "verðbólga", "verdbolga", "verdbólga",
        "atvinnuleysi", "laun", "hagstofa"
    ]
    needs_hagstofa = any(kw in q for kw in hagstofa_keywords)

    # 1. Legal RAG hefur áfram forgang fyrir legal domain
    rag_result = await _get_rag_context(query, domain)
    if rag_result.get("text"):
        return rag_result

    citations = []
    lines = []

    # 2. Hagstofa fyrst fyrir mannfjölda/efnahag
    if needs_hagstofa:
        try:
            from tools.sources.hagstofa_source import fetch_hagstofa
            hag = await fetch_hagstofa(query, 5)
            hag_citations = hag.get("citations", [])
            if hag_citations:
                citations.extend(hag_citations)
                lines.append("[Hagstofa Íslands]")
                for c in hag_citations:
                    title = c.get("title", "Hagstofa")
                    url = c.get("url", "")
                    snippet = c.get("snippet", "")
                    lines.append(f"* {title}: {url}")
                    if snippet:
                        lines.append(f"  {snippet}")
        except Exception as e:
            logger.error(f"[87E] Hagstofa fetch failed: {e}")

    # 3. Web search sem secondary context
    try:
        from tools.search_web_multi import search_web_multi
        res = await search_web_multi(query, max_results=6)
        web_citations = res.get("citations", [])
        
        if web_citations:
            if lines:
                lines.append("")
            lines.append("[Vefleit - Mojeek]")
            for c in web_citations:
                title = c.get("title", "Heimild")
                url = c.get("url", "")
                snippet = c.get("snippet", "")
                lines.append(f"* {title}: {url}")
                if snippet:
                    lines.append(f"  {snippet}")
            citations.extend(web_citations)
    except Exception as e:
        logger.error(f"[87E] Web search failed: {e}")

    if not citations:
        return {"text": "", "citations": []}

    return {
        "text": "\n".join(lines),
        "citations": citations
    }

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
            return (re.sub(r"<think>.*?</think>", "", d["choices"][0]["message"]["content"], flags=re.DOTALL).strip(), VAULT_LOCAL_MODEL, d.get("usage", {}))
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
                return (re.sub(r"<think>.*?</think>", "", d["choices"][0]["message"]["content"], flags=re.DOTALL).strip(), m_p, d.get("usage", {}))
        except Exception as e:
            logger.error(f"General chain error: {e}")
    return (None, None, None)


HALLUCINATED_PATTERNS = [
    r"https?://[^\s]*openai\.com[^\s]*",
    r"https?://[^\s]*chatgpt\.com[^\s]*",
    r"https?://[^\s]*example\.com[^\s]*",
    r"samkvæmt\s+OpenAI",
    r"samkvæmt\s+ChatGPT",
]

def _build_deterministic_fallback(citations: list) -> str:
    if citations:
        top = citations[:3]
        bullets = []
        for c in top:
            title = c.get("title") or "Heimild"
            snippet = (c.get("snippet") or "").strip()
            if snippet:
                bullets.append(f"- {title}: {snippet}")
            else:
                bullets.append(f"- {title}")
        return "Ég get ekki staðfest svarið nægilega vel út frá tiltækum heimildum. Hér eru áreiðanlegustu heimildirnar sem fundust:\n" + "\n".join(bullets)
    return "Ég get ekki staðfest svarið nægilega vel út frá tiltækum heimildum."


def _extract_legal_tokens(citations: list) -> list:
    """Dragur laganumer og artal ur raunverulegum citations — Opus P4."""
    import re
    tokens = set()
    for cit in (citations or [])[:10]:
        for field in ('title', 'citation_full', 'snippet', 'section'):
            val = (cit.get(field) or '').strip()
            if not val:
                continue
            # Laganumer: nr. 123, nr. 123/2021, 2021 nr. 123
            for m in re.finditer(r'(?:nr\.?\s*)?(\d{1,4})\s*(?:/\s*(\d{4}))?', val, flags=re.IGNORECASE):
                if m.group(2):
                    tokens.add(f'{m.group(1)}/{m.group(2)}')
                elif len(m.group(1)) <= 3:
                    tokens.add(m.group(1))
            # Artol: 1944, 1991, 2018, etc.
            for m in re.finditer(r'((?:1[89]|20)\d{2})', val):
                tokens.add(m.group(1))
    return list(tokens)


def _verify_cited_laws(response_text: str, citations: list) -> tuple[bool, str]:
    """Athugar hvort laganúmer sem nefnd eru í svari séu í veittum heimildum.
    Mýkri útgáfa: ef bæði tölur (t.d. 45 OG 2007) finnast í einhverri heimild, telst hún rétt.
    """
    import re
    # Finna pör af tölum (t.d. 45/2007 eða 2007 nr. 45)
    pairs = re.findall(r'(\d{2,4})\s*(?:/|nr\.?)\s*(\d{4})', response_text)
    for a, b in pairs:
        found_pair = False
        for c in citations:
            combined = ' '.join([str(c.get(f, '')) for f in ('title', 'citation_full', 'snippet', 'section')])
            if a in combined and b in combined:
                found_pair = True
                break
        if not found_pair:
            return False, f"Ógrundað laganúmer: {a}/{b}."
    return True, ""

def _verify_cited_articles(response_text: str, citations: list) -> tuple[bool, str]:
    """Athugar hvort greinarnúmer sem nefnd eru í svari séu í veittum heimildum."""
    import re
    cited_articles = set(re.findall(r'(\d+)\s*\.\s*gr', response_text))
    if not cited_articles:
        return True, ""
    doc_articles = set()
    for c in citations:
        snippet = (c.get('snippet') or c.get('text') or '').strip()
        doc_articles.update(re.findall(r'(\d+)\s*\.\s*gr', snippet))
        title = (c.get('title') or '').strip()
        doc_articles.update(re.findall(r'(\d+)\s*\.\s*gr', title))
    missing = cited_articles - doc_articles
    if missing:
        return False, f"Ógrundaðar tilvísanir í greinar: {', '.join(sorted(missing))}. gr."
    return True, ""

def _validate_response(response_text: str, citations: list) -> tuple[bool, str]:
    text = (response_text or "").strip()
    if not text:
        return False, _build_deterministic_fallback(citations)

    lowered = text.lower()
    for pattern in HALLUCINATED_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return False, _build_deterministic_fallback(citations)

    if not citations:
        return False, _build_deterministic_fallback([])
    if citations:
        source_titles = [
            (c.get("title") or "").strip()
            for c in citations
            if (c.get("title") or "").strip()
        ]
        if source_titles:
            # Athuga bæði title, citation_full, og section
            source_strings = []
            for c in citations[:5]:
                source_strings.append((c.get("title") or "").strip())
                source_strings.append((c.get("citation_full") or "").strip())
                source_strings.append((c.get("section") or "").strip())
            mentions_any_source = any(
                s.lower() in lowered
                for s in source_strings
                if len(s) > 3  # Sleppa tómum/of stuttum
            )
            has_generic_grounding = any(
                marker in lowered for marker in [
                    "samkvæmt heimild",
                    "samkvæmt gögnum",
                    "samkvæmt upplýsingum",
                    "heimildir",
                    "samkvæmt hagstofu",
                    "samkvæmt lögum",
                ]
            )
            # Opus P4: Draga laganumer/artol ur raunverulegum citations
            citation_tokens = _extract_legal_tokens(citations)
            has_citation_token_grounding = any(
                tok in lowered
                for tok in citation_tokens
                if len(tok) >= 2  # Sleppa of stuttum
            ) if citation_tokens else False
            if not mentions_any_source and not has_generic_grounding and not has_citation_token_grounding and len(text) > 280:
                return False, _build_deterministic_fallback(citations)

    # G0: sannreyna að greinarnúmer sem nefnd eru í svari séu í veittum heimildum
    article_ok, article_msg = _verify_cited_articles(text, citations)
    if not article_ok:
        return False, _build_deterministic_fallback(citations)
    # G1: sannreyna að laganúmer sem nefnd eru í svari séu í veittum heimildum
    laws_ok, laws_msg = _verify_cited_laws(text, citations)
    if not laws_ok:
        return False, _build_deterministic_fallback(citations)

    return True, text

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
    final_citations = search_res["citations"]
    
    # Kalla á YfirErindreka gegnum miðlægt fall
    from core.agents.call_orchestrator import call_orchestrator
    result = await call_orchestrator(query, tier, attached_files,
                                     search_res["text"], final_citations,
                                     file_context, domain)
    
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
    
    # Skila svari með server-side guard gegn uppspunnum heimildum
    cleaned = re.sub(r"<think>.*?</think>", "", result.response or "", flags=re.DOTALL).strip()
    is_valid, guarded_response = _validate_response(cleaned, final_citations)
    
    if not is_valid:
        logger.warning("[Guard] VitansErindreki svar var hafnað, notað determinískt fallback.")
    
    return JSONResponse(content={
        "success": True,
        "grounding_ok": is_valid,
        "response": guarded_response,
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




