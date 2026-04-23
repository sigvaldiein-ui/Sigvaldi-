"""
Sprint 65 Fasa 2 — Minimal OpenRouter client for intent fallback.

Scope:
- Single function: call_openrouter(model, prompt, timeout) -> str
- JSON mode requested when supported (Gemini Flash, GPT-4o-mini, Claude 3.5).
- Hard timeout cap 5s regardless of caller arg.
- Logs: model, latency_ms, prompt_tokens est, cost estimate (USD).
- Fails loud on missing API key; fails with raised exception on HTTP/timeout
  so caller (refine_with_llm) can fail-closed.

Not scope (S66):
- Retry logic, circuit breaker, semaphore, queue.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

import requests
from core.llm_concurrency import llm_guard

log = logging.getLogger("llm_client")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_HARD_TIMEOUT_CAP_S = 5.0

# Rough per-1M-token USD pricing (input+output blended). Used for log estimate only.
# Source: OpenRouter public pricing snapshot, kept loose on purpose.
_COST_PER_1K_TOKENS = {
    "google/gemini-2.5-flash":       0.00015,
    "anthropic/claude-3.5-haiku":    0.00100,
    "openai/gpt-4o-mini":            0.00060,
}

_JSON_MODE_MODELS = {
    "google/gemini-2.5-flash",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
}


def _require_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    return key


def _estimate_cost(model: str, prompt_chars: int, response_chars: int) -> float:
    # ~4 chars per token heuristic
    tokens = (prompt_chars + response_chars) / 4.0
    rate = _COST_PER_1K_TOKENS.get(model, 0.0005)
    return round((tokens / 1000.0) * rate, 6)


def call_openrouter(
    model: str,
    prompt: str,
    timeout: float = 3.0,
    system: Optional[str] = None,
    caller: str = "openrouter",
    request_id: Optional[str] = None,
) -> str:
    """
    Synchronous OpenRouter chat completion. Returns assistant text content.
    Raises on HTTP error, timeout, or bad payload.
    """
    api_key = _require_key()
    timeout = min(max(float(timeout), 0.5), _HARD_TIMEOUT_CAP_S)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 300,
    }
    if model in _JSON_MODE_MODELS:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alvitur.local",
        "X-Title": "Alvitur-Intent-Fallback",
    }

    t0 = time.time()
    with llm_guard(caller=caller, request_id=request_id):
        resp = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
        )
    latency_ms = int((time.time() - t0) * 1000)
    resp.raise_for_status()
    data = resp.json()

    try:
        content = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Bad OpenRouter payload: {e}")

    cost = _estimate_cost(model, len(prompt), len(content))
    log.info(
        "openrouter call model=%s latency_ms=%d prompt_chars=%d resp_chars=%d cost_usd=%.6f",
        model, latency_ms, len(prompt), len(content), cost,
    )
    # Mirror to stderr so it shows in terminal even without logging config
    print(
        f"[llm_client] model={model} latency_ms={latency_ms} "
        f"prompt_chars={len(prompt)} resp_chars={len(content)} cost_usd={cost:.6f}",
        flush=True,
    )
    return content
