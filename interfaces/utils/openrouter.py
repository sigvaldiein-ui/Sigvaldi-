"""OpenRouter balance check, wallet preflight, intent logging for Alvitur.

Sprint 71 Track A.4c — extracted from interfaces/web_server.py.
"""
import logging
import os
from pathlib import Path

from fastapi import HTTPException

from interfaces.utils.quota import WALLET_MIN_USD, WALLET_MIN_VAULT_USD

logger = logging.getLogger("alvitur.web")



_WALLET_TTL = 60  # sekúndur
_wallet_cache: dict = {"balance": None, "ts": 0.0}

def _get_openrouter_balance():
    import time as _t, requests as _rq
    now = _t.time()
    if _wallet_cache["balance"] is not None and now - _wallet_cache["ts"] < _WALLET_TTL:
        return _wallet_cache["balance"]
    try:
        _k = os.environ.get("OPENROUTER_API_KEY", "")
        r = _rq.get("https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {_k}"}, timeout=5)
        if r.status_code == 200:
            d = r.json().get("data", {})
            limit = d.get("limit")
            if limit is not None:
                bal = round(float(limit) - float(d.get("usage") or 0), 4)
            else:
                bal = 100.0
            _wallet_cache["balance"] = bal
            _wallet_cache["ts"] = now
            return bal
    except Exception:
        pass
    return None

def _wallet_preflight(is_vault=False):
    bal = _get_openrouter_balance()
    if bal is None: return
    threshold = WALLET_MIN_VAULT_USD if is_vault else WALLET_MIN_USD
    if bal < threshold:
        logger.warning(f"Wallet circuit breaker: balance=${bal:.2f} < ${threshold:.2f}")
        raise HTTPException(status_code=503,
            detail="Þ jónustan er tímabundið ótilðæk. Reyndu aftur eftir augnablik.")

# ───────────────────────────────────────────────────────────
SECURE_DOCS_DIR = Path("/workspace/Sigvaldi-/data/secure_docs")
SECURE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
MAX_PDF_SIZE = 20 * 1024 * 1024  # Sprint 27 S2: raised to 20 MB



_INTENT_AVAILABLE = False
_classify_intent = None

def _log_intent(endpoint: str, query, filename, file_size, tier) -> None:
    """Sprint 64 B2-V2: observability hook. NEVER raises."""
    if not _INTENT_AVAILABLE or _classify_intent is None:
        return
    try:
        ir = _classify_intent(query=query, filename=filename,
                              file_size=file_size, tier=tier)
        logger.info(
            f"[INTENT] endpoint={endpoint} domain={ir.domain} "
            f"depth={ir.reasoning_depth} conf={ir.confidence_score:.2f} "
            f"sens={ir.sensitivity} adapter={ir.adapter_hint} "
            f"src={ir.source_hint}"
        )
    except Exception as _ie:
        logger.warning(f"[INTENT] classify failed on {endpoint}: {type(_ie).__name__}: {_ie}")

