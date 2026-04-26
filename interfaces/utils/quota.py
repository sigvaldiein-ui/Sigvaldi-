"""Quota tracking and beta-tier logic for Alvitur.

Sprint 71 Track A.4c — extracted from interfaces/web_server.py.
"""
import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger("alvitur.web")

WALLET_MIN_USD       = float(os.environ.get("WALLET_MIN_USD", "5.0"))
WALLET_MIN_VAULT_USD = float(os.environ.get("WALLET_MIN_VAULT_USD", "10.0"))

# PLG quota tracker (IP-based, in-memory)
_quota_tracker_chat: dict = {}  # /api/chat quota per IP
_quota_tracker_doc: dict = {}   # /api/analyze-document quota per IP
FREE_QUOTA = 5



# -- Sprint 66 pre-A hotfix: persist _beta_tracker across restarts --
import json as _json_bt
import os as _os_bt
import time as _time_bt
from pathlib import Path as _Path_bt

_BETA_TRACKER_FILE = _Path_bt(_os_bt.getenv("BETA_TRACKER_PATH", "data/beta_tracker.json"))

def _load_beta_tracker_from_disk() -> dict:
    try:
        if not _BETA_TRACKER_FILE.exists():
            return {}
        raw = _json_bt.loads(_BETA_TRACKER_FILE.read_text(encoding="utf-8"))
        now = _time_bt.time()
        # TODO(S66-A): replace with BETA_DURATION_SEC module const (defined below)
        _DUR = int(_os_bt.getenv("BETA_DURATION_SEC_OVERRIDE", 7 * 24 * 3600))
        return {ip: float(ts) for ip, ts in raw.items() if now - float(ts) <= _DUR}
    except Exception as e:
        try:
            logger.warning(f"[BETA] load failed: {type(e).__name__}: {e}")
        except Exception:
            pass
        return {}

def _save_beta_tracker_to_disk(tracker: dict) -> None:
    try:
        _BETA_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _BETA_TRACKER_FILE.with_suffix(".tmp")
        tmp.write_text(_json_bt.dumps(tracker, indent=2), encoding="utf-8")
        tmp.replace(_BETA_TRACKER_FILE)
    except Exception as e:
        try:
            logger.warning(f"[BETA] save failed: {type(e).__name__}: {e}")
        except Exception:
            pass
# -- /persist helpers --

# ── Sprint 62: Beta tracker ──
# Beta-tier via human phrase in chat: "Sigvaldi sendi mig" (7-day renewable)
_beta_tracker: dict[str, float] = {}   # IP → promotion_timestamp (epoch sec)
BETA_DURATION_SEC = 7 * 24 * 3600      # 7 dagar
BETA_FRASAR = (
    "sigvaldi sendi mig",
    "ég er beta notandi",
    "beta aðgangur",
    "beta adgangur",
)

def _er_beta_fras(text: str) -> bool:
    """Satt ef notendatexti inniheldur einhvern viðurkenndan beta-frasa."""
    if not text:
        return False
    lower = text.lower()
    return any(fras in lower for fras in BETA_FRASAR)

def _er_beta_ip(ip: str) -> bool:
    """Satt ef IP er í beta-tier (innan 7 daga frá promotion)."""
    import time as _t
    ts = _beta_tracker.get(ip)
    if ts is None:
        return False
    if _t.time() - ts > BETA_DURATION_SEC:
        _beta_tracker.pop(ip, None)
        return False
    return True

def _promota_beta(ip: str) -> None:
    """Setur IP í beta-tier núna (eða endurnýjar)."""
    import time as _t
    _beta_tracker[ip] = _t.time()
    _save_beta_tracker_to_disk(_beta_tracker)
# ── /Sprint 62 Beta tracker ──
_beta_tracker.update(_load_beta_tracker_from_disk())
_wallet_cache: dict  = {"balance": None, "ts": 0.0}
_WALLET_TTL          = 120
