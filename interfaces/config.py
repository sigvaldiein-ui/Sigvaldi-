# interfaces/config.py
"""
Sprint 53b — Miðlægar módel stillingar.

Ein staðurinn þar sem öll módel env var eru lesin.
Öll önnur interfaces skrár nota þessa module í stað þess að lesa env vars sjálf.

Módel (Sprint 53a):
  Leið A  — minimax/minimax-m2.5   (general tier)
  Leið B  — minimax/minimax-m2.7   (vault tier)
  Classify — qwen/qwen3.5-27b      (domain classification)
  Polish   — deepseek/deepseek-chat-v3-0324  (íslenska fágun)
"""
import os

# ── Módel routing ─────────────────────────────────────────────────────────────
MODEL_LEIDA_A: str = os.environ.get("ALVITUR_MODEL_LEIDA_A", "minimax/minimax-m2.5")
MODEL_LEIDA_B: str = os.environ.get("ALVITUR_MODEL_LEIDA_B", "minimax/minimax-m2.7")
CLASSIFY_MODEL: str = os.environ.get("ALVITUR_CLASSIFY_MODEL", "qwen/qwen3.5-27b")
POLISH_MODEL: str = os.environ.get("ALVITUR_POLISH_MODEL", "deepseek/deepseek-chat-v3-0324")

# ── Hjálparfall ───────────────────────────────────────────────────────────────
def get_model(tier: str) -> str:
    """Skilar réttu módeli eftir tier."""
    return MODEL_LEIDA_B if tier == "vault" else MODEL_LEIDA_A
