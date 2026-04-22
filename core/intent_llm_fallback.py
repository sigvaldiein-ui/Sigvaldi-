"""
Sprint 65 Fasa 2 — LLM fallback for intent_gateway.

Contract:
- Called ONLY when rule-based confidence < threshold (default 0.6).
- Returns SAME IntentResult schema — no downstream changes.
- Fails closed: on any error/timeout, returns the original rule-based result.
- Guarded by env flag INTENT_LLM_FALLBACK_ENABLED (default: "0").

S66 coupling:
- LLM call will later be wrapped in asyncio.Semaphore(4) from queue module.
- Today: direct sync call with hard timeout.
"""

from __future__ import annotations

import json
import os
import time
from typing import Optional

from models.intent import IntentResult

# Env-driven config (all optional)
_ENABLED_ENV = "INTENT_LLM_FALLBACK_ENABLED"
_MODEL_ENV = "INTENT_LLM_FALLBACK_MODEL"
_TIMEOUT_ENV = "INTENT_LLM_FALLBACK_TIMEOUT_S"
_THRESHOLD_ENV = "INTENT_LLM_FALLBACK_THRESHOLD"

_DEFAULT_MODEL = "google/gemini-2.5-flash"
_DEFAULT_TIMEOUT = 3.0
_DEFAULT_THRESHOLD = 0.6

_ALLOWED_DOMAINS = {"general", "legal", "financial", "technical", "public"}
_ALLOWED_DEPTHS = {"fast", "standard", "deep"}


def is_enabled() -> bool:
    return os.getenv(_ENABLED_ENV, "0").lower() in ("1", "true", "yes", "on")


def threshold() -> float:
    try:
        return float(os.getenv(_THRESHOLD_ENV, _DEFAULT_THRESHOLD))
    except ValueError:
        return _DEFAULT_THRESHOLD


def should_fallback(result: IntentResult) -> bool:
    if not is_enabled():
        return False
    return result.confidence_score < threshold()


def _build_prompt(query: Optional[str], filename: Optional[str],
                  file_size: Optional[int], rule_result: IntentResult) -> str:
    # v2: no rule-based leak, explicit depth rules, few-shot, confidence calibration
    return (
        "You classify Icelandic user queries. Output ONE JSON object, nothing else.\n"
        "Schema: {\"domain\": str, \"reasoning_depth\": str, \"confidence_score\": float}\n"
        f"domain in {sorted(_ALLOWED_DOMAINS)}\n"
        f"reasoning_depth in {sorted(_ALLOWED_DEPTHS)}\n"
        "confidence_score in [0.0, 1.0].\n\n"
        "Depth rules:\n"
        "- fast: short factual query (<80 chars), no file, simple lookup.\n"
        "- standard: normal explanation or mid-size file (<100KB).\n"
        "- deep: long query (>200 chars), large file (>=100KB), or query asks for 'itarleg', 'greining', 'sundurlidad'.\n\n"
        "Confidence calibration:\n"
        "- Return >=0.85 when the answer is obvious from query/file.\n"
        "- Return 0.5-0.8 when plausible but some signals missing.\n"
        "- Return <=0.45 only when query is genuinely ambiguous or empty.\n\n"
        "Examples:\n"
        'Q: "Hvad er hofudborg Islands?" F: none -> {"domain":"general","reasoning_depth":"fast","confidence_score":0.95}\n'
        'Q: "Greindu arsreikning 2024 itarlega" F: arsreikningur.xlsx 204800B -> {"domain":"financial","reasoning_depth":"deep","confidence_score":0.92}\n'
        'Q: "tja" F: none -> {"domain":"general","reasoning_depth":"fast","confidence_score":0.3}\n'
        'Q: none F: skyrsla.pdf 51200B -> {"domain":"general","reasoning_depth":"standard","confidence_score":0.7}\n\n'
        f"Now classify:\n"
        f"Q: {query or '(none)'}\n"
        f"F: {filename or '(none)'} {file_size if file_size is not None else ''}{'B' if file_size else ''}\n"
        "Output JSON only."
    )


def _parse_response(raw: str) -> Optional[dict]:
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    d = data.get("domain")
    r = data.get("reasoning_depth")
    c = data.get("confidence_score")
    if d not in _ALLOWED_DOMAINS:
        return None
    if r not in _ALLOWED_DEPTHS:
        return None
    try:
        c = float(c)
    except Exception:
        return None
    c = max(0.0, min(1.0, c))
    return {"domain": d, "reasoning_depth": r, "confidence_score": round(c, 2)}


def refine_with_llm(
    query: Optional[str],
    filename: Optional[str],
    file_size: Optional[int],
    rule_result: IntentResult,
) -> IntentResult:
    """
    Call LLM to refine low-confidence rule-based result.
    Fails closed: returns rule_result on any error.
    """
    if not should_fallback(rule_result):
        return rule_result

    try:
        # Deferred import so module loads even without OpenRouter client
        from core.llm_client import call_openrouter  # type: ignore
    except Exception:
        return rule_result

    model = os.getenv(_MODEL_ENV, _DEFAULT_MODEL)
    try:
        timeout = float(os.getenv(_TIMEOUT_ENV, _DEFAULT_TIMEOUT))
    except ValueError:
        timeout = _DEFAULT_TIMEOUT

    prompt = _build_prompt(query, filename, file_size, rule_result)

    t0 = time.time()
    try:
        raw = call_openrouter(model=model, prompt=prompt, timeout=timeout)
    except Exception:
        return rule_result
    elapsed = time.time() - t0

    parsed = _parse_response(raw or "")
    if not parsed:
        return rule_result

    # Preserve adapter_hint, sensitivity, source_hint from rule-based.
    return IntentResult(
        domain=parsed["domain"],
        reasoning_depth=parsed["reasoning_depth"],
        adapter_hint=rule_result.adapter_hint,
        confidence_score=parsed["confidence_score"],
        sensitivity=rule_result.sensitivity,
        source_hint=rule_result.source_hint,
    )
