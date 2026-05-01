"""Runtime globals — brotið úr web_server.py (Sprint 71 Track A.4d).

ATH: Þetta er runtime convenience layer, EKKI authoritative config.
Framtíðar-refactor ætti að sækja defaults úr interfaces.config.
"""
import asyncio
import os

_VAULT_SEMAPHORE_WS = asyncio.Semaphore(2)
_MODEL_LEIDA_A = os.getenv("MODEL_LEIDA_A", "openai/gpt-4o")
_MODEL_LEIDA_B = os.getenv("MODEL_LEIDA_B", "anthropic/claude-sonnet-4-20250514")
