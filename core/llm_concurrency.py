"""LLM concurrency guard - Sprint 66 A1.

Shared primitive for all LLM calls. Phased integration:
A1-iii integrates into llm_client.py + intent path only.

Env:
  INTENT_LLM_MAX_CONCURRENT  int   default=4   max concurrent LLM calls (>=1)
  LLM_CONCURRENCY_ENABLED    bool  default=true  feature flag
  LLM_CONCURRENCY_TIMEOUT    float default=8.0   acquire timeout sec (>0)

API:
  with llm_guard(caller="intent", request_id=rid):
      response = llm_call(...)
  with llm_guard(bypass=True):     # emergency per-caller escape
      response = llm_call(...)

Metrics (logged):
  [LLM_GUARD] acquired   caller=... request_id=... active_count=...
  [LLM_GUARD] released   caller=... request_id=... held_ms=...
  [LLM_GUARD] timeout    caller=... request_id=... waited_ms=...
  [LLM_GUARD] bypass     caller=... request_id=...

Rollback anchor: sprint66-pre-a-hotfix (f52f6b7).
"""
import os
import time
import threading
import logging
import contextlib
from typing import Optional

logger = logging.getLogger("llm_concurrency")

# Env reads at import time
_MAX_CONCURRENT = int(os.getenv("INTENT_LLM_MAX_CONCURRENT", "4"))
_ENABLED = os.getenv("LLM_CONCURRENCY_ENABLED", "true").lower() == "true"
_TIMEOUT = float(os.getenv("LLM_CONCURRENCY_TIMEOUT", "8.0"))

# Startup validation (fail-fast)
if _MAX_CONCURRENT < 1:
    raise ValueError(
        f"INTENT_LLM_MAX_CONCURRENT must be >= 1 (got {_MAX_CONCURRENT})"
    )
if _TIMEOUT <= 0:
    raise ValueError(
        f"LLM_CONCURRENCY_TIMEOUT must be > 0 (got {_TIMEOUT})"
    )

_semaphore = threading.BoundedSemaphore(_MAX_CONCURRENT) if _ENABLED else None
_active_count = 0
_active_lock = threading.Lock()


@contextlib.contextmanager
def llm_guard(caller: str = "unknown",
              request_id: Optional[str] = None,
              bypass: bool = False):
    """Acquire semaphore before LLM call; release on exit.

    Caller exceptions propagate unchanged (only release is guaranteed
    via the contextmanager's finally clause).

    Known limitation: threading.BoundedSemaphore is not strictly fair
    (no FIFO guarantee). Starvation under heavy load is possible but
    bounded by timeout. If observed, migrate to queue.Queue-based fair
    semaphore in S67 (see docs/SPRINT66_A1_DESIGN.md section 10).
    """
    global _active_count
    rid = request_id or "-"

    if not _ENABLED or bypass:
        if bypass:
            logger.info(f"[LLM_GUARD] bypass caller={caller} request_id={rid}")
        yield
        return

    t0 = time.monotonic()
    acquired = _semaphore.acquire(timeout=_TIMEOUT)
    if not acquired:
        waited_ms = int((time.monotonic() - t0) * 1000)
        logger.error(
            f"[LLM_GUARD] timeout caller={caller} request_id={rid} "
            f"waited_ms={waited_ms}"
        )
        raise TimeoutError(
            f"llm_guard acquire timeout ({_TIMEOUT}s) for {caller}"
        )

    with _active_lock:
        _active_count += 1
        current_active = _active_count
    logger.info(
        f"[LLM_GUARD] acquired caller={caller} request_id={rid} "
        f"active_count={current_active}"
    )
    t_held = time.monotonic()
    try:
        yield
    finally:
        held_ms = int((time.monotonic() - t_held) * 1000)
        with _active_lock:
            _active_count -= 1
        _semaphore.release()
        logger.info(
            f"[LLM_GUARD] released caller={caller} request_id={rid} "
            f"held_ms={held_ms}"
        )


def active_count() -> int:
    """Current number of acquired guards. For health endpoint / debugging."""
    with _active_lock:
        return _active_count


def max_concurrent() -> int:
    """Configured max. For health endpoint / debugging."""
    return _MAX_CONCURRENT


def is_enabled() -> bool:
    """Feature flag state. For health endpoint / debugging."""
    return _ENABLED
