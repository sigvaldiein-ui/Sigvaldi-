# interfaces/config.py - Sprint 61
"""Leid A/B adskilnadur: Leid A = OpenRouter chain, Leid B = local sovereign vLLM."""
import os

# Leid A: OpenRouter ZDR fallback chain (general tier)
MODEL_LEIDA_A_PRIMARY: str = os.environ.get("ALVITUR_MODEL_LEIDA_A_PRIMARY", "anthropic/claude-3.5-haiku")
MODEL_LEIDA_A_SECONDARY: str = os.environ.get("ALVITUR_MODEL_LEIDA_A_SECONDARY", "anthropic/claude-sonnet-4.5")
MODEL_LEIDA_A_TERTIARY: str = os.environ.get("ALVITUR_MODEL_LEIDA_A_TERTIARY", "openai/gpt-4o-mini")

# Leid B: LOCAL SOVEREIGN (vault tier) - NO cloud fallback
VAULT_LOCAL_URL: str = os.environ.get("ALVITUR_VAULT_LOCAL_URL", "http://localhost:8002/v1/chat/completions")
VAULT_LOCAL_MODEL: str = os.environ.get("ALVITUR_VAULT_LOCAL_MODEL", "/workspace/models/qwen3-32b-awq")
VAULT_LOCAL_TIMEOUT: int = int(os.environ.get("ALVITUR_VAULT_LOCAL_TIMEOUT", "60"))
VAULT_MAX_INPUT_TOKENS: int = int(os.environ.get("ALVITUR_VAULT_MAX_INPUT_TOKENS", "7000"))

# Classify + Polish (Leid A only)
CLASSIFY_MODEL: str = os.environ.get("ALVITUR_CLASSIFY_MODEL", "qwen/qwen3.5-27b")
POLISH_MODEL: str = os.environ.get("ALVITUR_POLISH_MODEL", "deepseek/deepseek-chat-v3-0324")

# Back-compat aliases (deprecated)
MODEL_LEIDA_A = MODEL_LEIDA_A_PRIMARY
MODEL_LEIDA_B = VAULT_LOCAL_MODEL

def get_model(tier: str) -> str:
    return MODEL_LEIDA_B if tier == "vault" else MODEL_LEIDA_A
