"""Health and diagnostics endpoints for Alvitur.

Sprint 71 Track A.4b — extracted from interfaces/web_server.py.

Endpoints:
- GET /api/health             — basic liveness check
- GET /api/health/detailed    — full system status (Sprint 69 H.1)
- GET /api/diagnostics        — runtime diagnostics
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("alvitur.web")
router = APIRouter()


# --- health ---
@router.get("/api/health")
async def health():
    """Heilsufarsskoðun — notað af monitoring og load balancer."""
    return JSONResponse(content={
        "status": "ok",
        "version": "sprint63-track-b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fasi": "production",
    })


# --- health_detailed ---
@router.get("/api/health/detailed")
async def health_detailed():
    """Raunverulegur health check fyrir alla Alvitur components."""
    import time, subprocess, os
    import httpx
    from datetime import datetime, timedelta
    start = time.time()

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "overall": "unknown",
        "components": {},
        "metrics": {},
        "errors_last_10min": 0,
    }

    # 1. FastAPI self
    report["components"]["fastapi"] = {
        "status": "ok",
        "pid": os.getpid(),
        "version": "sprint63-track-b",
    }

    # 2. vLLM local (port 8002)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:8002/v1/models")
            if r.status_code == 200:
                models = r.json().get("data", [])
                report["components"]["vllm"] = {
                    "status": "ok",
                    "models_loaded": [m.get("id") for m in models[:3]],
                    "latency_ms": int((time.time() - start) * 1000),
                }
            else:
                report["components"]["vllm"] = {"status": "degraded", "http_code": r.status_code}
    except Exception as e:
        report["components"]["vllm"] = {"status": "down", "error": f"{type(e).__name__}: {e}"}

    # 3. OpenRouter
    try:
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key or len(key) < 40:
            report["components"]["openrouter"] = {"status": "misconfigured", "error": "API key missing"}
        else:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {key}"},
                )
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    report["components"]["openrouter"] = {
                        "status": "ok",
                        "credits_remaining": data.get("limit_remaining"),
                        "rate_limit": data.get("rate_limit", {}).get("requests"),
                    }
                else:
                    report["components"]["openrouter"] = {"status": "auth_failed", "http_code": r.status_code}
    except Exception as e:
        report["components"]["openrouter"] = {"status": "unreachable", "error": f"{type(e).__name__}: {e}"}

    # 4. Disk space
    try:
        result = subprocess.run(["df", "-h", "/workspace"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            pct = int(parts[4].rstrip("%"))
            report["components"]["disk"] = {
                "status": "ok" if pct < 90 else "warning",
                "used": parts[2],
                "available": parts[3],
                "percent_used": parts[4],
            }
    except Exception as e:
        report["components"]["disk"] = {"status": "error", "error": str(e)}

    # 5. GPU VRAM
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        parts = result.stdout.strip().split(", ")
        if len(parts) == 3:
            used, total, free = int(parts[0]), int(parts[1]), int(parts[2])
            pct = (used / total) * 100
            report["components"]["gpu"] = {
                "status": "ok" if pct < 95 else "critical",
                "used_mib": used,
                "total_mib": total,
                "free_mib": free,
                "percent_used": round(pct, 1),
            }
    except Exception as e:
        report["components"]["gpu"] = {"status": "error", "error": str(e)}

    # 6. Error count sidastu 10 min
    try:
        result = subprocess.run(
            ["tail", "-n", "500", "/workspace/web_server.log"],
            capture_output=True, text=True, timeout=3
        )
        error_count = sum(
            1 for line in result.stdout.split("\n")
            if any(k in line for k in ("ERROR", "Traceback", "Exception"))
        )
        report["errors_last_10min"] = error_count
    except Exception:
        report["errors_last_10min"] = -1

    # 7. Overall status
    statuses = [c.get("status", "unknown") for c in report["components"].values()]
    if any(s == "down" for s in statuses):
        report["overall"] = "critical"
    elif any(s in ("degraded", "warning", "error", "critical") for s in statuses):
        report["overall"] = "degraded"
    elif all(s == "ok" for s in statuses):
        report["overall"] = "healthy"
    else:
        report["overall"] = "unknown"

    report["metrics"]["check_latency_ms"] = int((time.time() - start) * 1000)
    return report



# --- diagnostics ---
@router.get("/api/diagnostics")
async def diagnostics():
    """Sprint 63 Track A5 + B3: Diagnostics — stöðu leiða og umhverfis."""
    import os as _os_d
    import time as _time_d
    _key = _os_d.environ.get("OPENROUTER_API_KEY", "")
    leid_a_enabled = bool(_key and len(_key) > 10 and not _key.startswith("sk-or-v1-BAD"))
    # Track B3: vLLM er á port 8002 (ekki 8001 sem var hardcoded default)
    _sovereign_url = _os_d.environ.get("SOVEREIGN_URL", "http://localhost:8002/v1/chat/completions")
    # Track B3: env flag + port
    _env_flag = _os_d.environ.get("ALVITUR_ENV", "prod")
    _port = int(_os_d.environ.get("ALVITUR_PORT", "8000"))
    try:
        uptime = int(_time_d.time() - _SERVER_START_TIME)
    except NameError:
        uptime = -1
    return JSONResponse(content={
        "status": "ok",
        "version": "sprint63-track-b",
        "env": _env_flag,
        "port": _port,
        "leid_a_enabled": leid_a_enabled,
        "leid_a_key_length": len(_key) if _key else 0,
        "leid_b_enabled": bool(_sovereign_url),
        "leid_b_url": _sovereign_url,
        "uptime_seconds": uptime,
        "loaded_env": bool(_key),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ─── Sprint 58+59: MCP Tools Endpoints ─────────────────────────────────────────

