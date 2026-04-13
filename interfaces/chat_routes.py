from fastapi import Request
from fastapi.responses import JSONResponse
import os, httpx, logging
logger = logging.getLogger("alvitur.web")

async def handle_chat(request: Request, query: str, tier: str = "general", attached_files: list | None = None):
    # Try local vLLM first (port 8002)
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post("http://localhost:8002/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [{"role":"user","content":query}],
                "max_tokens": 1024, "temperature": 0.2
            })
            r.raise_for_status()
            ans = r.json()["choices"][0]["message"]["content"]
            return JSONResponse(content={"success": True, "summary": ans, "pipeline": "local_vllm"})
    except Exception as e:
        logger.warning("Local failed: %s", e)
    
    # Fallback to OpenRouter
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return JSONResponse(status_code=503, content={"error": "No LLM available"})
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://alvitur.is"},
                json={"model": "openai/gpt-4o-mini", "messages": [{"role":"user","content":query}], "max_tokens": 1024})
            r.raise_for_status()
            ans = r.json()["choices"][0]["message"]["content"]
            return JSONResponse(content={"success": True, "summary": ans, "pipeline": "openrouter"})
    except Exception as e:
        logger.error("Chat error: %s", e)
        return JSONResponse(status_code=502, content={"error": str(e)})
