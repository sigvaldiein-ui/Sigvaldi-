from fastapi import Request
from fastapi.responses import JSONResponse
import os, httpx, logging, json
from datetime import datetime, timezone

logger = logging.getLogger("alvitur.web")

def _get_rag_context(query: str, domain: str) -> str:
    if domain != "legal": return ""
    keywords = ["persónuvernd", "gagnavernd", "lög", "réttur", "heimild", "lag", "samþykki"]
    if any(kw in query.lower() for kw in keywords):
        return """
[Heimildir]
• Persónuverndarlög nr. 90/2018, 15. gr.: Réttur aðila til upplýsinga um meðferð persónuupplýsinga.
• Upplýsingalög nr. 142/2012: Almennur aðgangur að opinberum gögnum.
"""
    return ""

async def handle_chat(request: Request, query: str, tier: str = "general", attached_files: list | None = None):
    files = attached_files or []
    
    # DEBUG logging
    logger.info(f"🔍 DEBUG: query='{query[:100]}...', tier='{tier}', files={len(files)}")
    
    domain = "legal" if any(kw in query.lower() for kw in ["lög", "lag", "réttur", "persónuvernd", "gagnavernd"]) else "general"
    rag = _get_rag_context(query, domain)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Búa til file context EF skrár eru til staðar
    file_context = ""
    if files:
        file_context = "\n\n[MEÐFYLGJANDI SKJÖL - NOTAÐU AÐEINS EF SPURNINGIN BEINIR ÞÉR ÞANGAÐ]:"
        for i, f in enumerate(files[:3], 1):  # Max 3 skrár til að spara tokens
            fname = f.get("filename", f"Skjal {i}")
            content = f.get("content", "")[:1500]  # Takmarka lengd
            file_context += f"\n--- {fname} ---\n{content}"
        file_context += "\n[ENDIR SKJALA]"
    
    # System prompt með STRANGRI skipun um að svara SPURNINGUNNI
    system = f"""Þú ert Alvitur, íslenskur sérfræðingur.
Dagsetning: {now_str}
{rag}
{file_context}

⭐⭐⭐ MİKILVÆGAST: ⭐⭐⭐
1. SPURNING NOTANDANS ER: "{query}"
2. Svaraðu BEINT þessari spurningu á íslensku.
3. Ef skrár eru meðfylgjandi, notaðu þær AÐEINS til að svara spurningunni — ekki lýsa þeim nema beðið sé um það.
4. Ekki endurskrifa skrár, ekki endurtaka innihald — svaraðu spurningunni.
5. Stutt, skýrt, faglegt svar.
⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐"""

    logger.info(f"🔍 DEBUG: LLM call - query='{query[:50]}...', has_files={bool(files)}")
    
    # 1. Prófa local vLLM
    try:
        async with httpx.AsyncClient(timeout=45.0) as c:
            payload = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"SPURNING: {query}\n\nSvaraðu beint og stutt á íslensku."}
                ],
                "max_tokens": 500, "temperature": 0.2, "top_p": 0.9
            }
            r = await c.post("http://localhost:8002/v1/chat/completions", json=payload)
            r.raise_for_status()
            ans = r.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"🔍 DEBUG: Response OK, len={len(ans)}")
            return JSONResponse(content={"success": True, "response": ans, "pipeline": "local_vllm", "domain": domain})
    except Exception as e:
        logger.warning(f"Local failed: {e}")
        
    # 2. Fallback á OpenRouter
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key: return JSONResponse(status_code=503, content={"error": "LLM unavailable"})
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://alvitur.is"},
                json={"model": "openai/gpt-4o-mini", "messages": [{"role": "system", "content": system}, {"role": "user", "content": f"SPURNING: {query}"}], "max_tokens": 500, "temperature": 0.2})
            r.raise_for_status()
            return JSONResponse(content={"success": True, "response": r.json()["choices"][0]["message"]["content"].strip(), "pipeline": "openrouter", "domain": domain})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return JSONResponse(status_code=502, content={"error": str(e)})
