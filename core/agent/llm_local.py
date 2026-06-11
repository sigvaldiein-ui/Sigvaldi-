"""Staðbundinn LLM klíent — kallar á Qwen í gegnum vLLM."""

import json
import httpx
from typing import Optional, List, Dict, Any

VLLM_URL = "http://localhost:8002/v1/chat/completions"
MODEL_NAME = "/workspace/models/qwen3-32b-awq"
TIMEOUT = 180

PLANNER_SYSTEM_PROMPT = """Þú ert skipulagsstjóri. Brjóttu verkefni niður í skref.
Tiltæk tól: draft_document, analyze_text, write_code, research, send_email (HITL).
Skilaðu AÐEINS JSON: {"steps": [{"tool": "...", "params": {...}}]}"""


async def call_qwen(system_prompt: str, user_message: str,
                    temperature: float = 0.3, max_tokens: int = 2048) -> Optional[str]:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(VLLM_URL, json=payload)
            if response.status_code != 200:
                print(f"[LLM] Villa: HTTP {response.status_code}")
                return None
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM] Villa: {e}")
        return None


async def plan_with_qwen(task_description: str) -> Optional[List[Dict[str, Any]]]:
    raw = await call_qwen(PLANNER_SYSTEM_PROMPT, f"Verkefni: {task_description}")
    if not raw:
        return None
    import re
    cleaned = raw.strip()
    # Fjarlægja <think> tag ef til staðar
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL).strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])
    try:
        return json.loads(cleaned).get("steps", [])
    except json.JSONDecodeError as e:
        print(f"[LLM] JSON villa: {e}")
        print(f"[LLM] Hrátt: {raw[:300]}")
        return None
