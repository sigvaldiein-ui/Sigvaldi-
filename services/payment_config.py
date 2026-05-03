#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
payment_handler.py
------------------
Straumur greiðslustjóri fyrir Mímir.
Notar Hosted Checkout API til að búa til greiðslulotu,
athuga stöðu og vinna úr webhook frá Straumi.

Höfundur: Per (Yfirverkfræðingur) skv. fyrirmælum Aðals Arkitektsins
Dagsetning: 2026-03-31 (Sprint 15.2)

STRAUMUR API SKJÖLUN:
- Hosted Checkout: https://docs.straumur.is/hosted-checkout/basic-checkout-request
- Status: https://docs.straumur.is/hosted-checkout/hosted-checkout-status
- Webhooks: https://docs.straumur.is/webhooks/payment/authorization-event
- HMAC: https://docs.straumur.is/webhooks/payment/hmac-validation
- API Keys: https://docs.straumur.is/get-started/api-keys

FLÆÐIÐ:
1. Notandi biður um áskrift → búa til checkout session
2. Straumur skilar URL → senda í Telegram sem inline takki
3. Notandi greiðir á Straumur síðu
4. Straumur sendir webhook → staðfesta HMAC → uppfæra gagnagrunn
5. Notandi fær premium aðgang

REGLUR:
- Allar upphæðir í minor units (ISK: 990 kr = 99000)
- STRAUMUR_API_KEY lesið úr config/.env
- STRAUMUR_TERMINAL_ID lesið úr config/.env
- STRAUMUR_HMAC_SECRET lesið úr config/.env
- ALDREI birta API lykla eða leyndarmál
"""

import os
import json
import hmac
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None
    print("⚠️  requests pakki vantar — keyra: pip install requests")

# --- Stillingar ---

# Lesa úr .env skrám á RunPod
ENV_SLOD = Path("/workspace/mimir_net/config/.env")

# Straumur API slóðir
# STAGING: https://checkout-api.staging.straumur.is/api/v1
# PROD:    https://checkout-api.straumur.is/api/v1
STRAUMUR_BASE_URL_STAGING = "https://checkout-api.staging.straumur.is/api/v1"
STRAUMUR_BASE_URL_PROD = "https://checkout-api.straumur.is/api/v1"

# Sjálfgefið: staging (breytt í PROD þegar tilbúið)
STRAUMUR_BASE_URL = STRAUMUR_BASE_URL_STAGING

# Verðskrá — upphæðir í minor units (ISK: krónutala × 100)
VERDSKRA = {
    "kynning":      {"nafn": "Kynningartilboð",       "verd_isk": 990,   "minor_units": 99000,   "timi_dagar": 30},
    "einstakling":  {"nafn": "Einstaklingsaðgangur",   "verd_isk": 1990,  "minor_units": 199000,  "timi_dagar": 30},
    "midgildi":     {"nafn": "Miðgildispakki",         "verd_isk": 4990,  "minor_units": 499000,  "timi_dagar": 30},
    "fyrirtaeki":   {"nafn": "Fyrirtækjapakki",        "verd_isk": 0,     "minor_units": 0,       "timi_dagar": 365},
}

# Return URL — notandi fer hingað eftir greiðslu
# TODO: Uppfæra þegar við höfum raunverulega return síðu
RETURN_URL = "https://t.me/AlviturBot"


def lesa_env_breyta(nafn: str) -> str:
    """
    Les umhverfisbreytu úr config/.env eða os.environ.
    Prófar fyrst os.environ, síðan .env skrá.
    Skilar tómu ef ekkert finnst.
    """
    # 1. Athuga os.environ fyrst
    gildi = os.environ.get(nafn, "")
    if gildi:
        return gildi

    # 2. Lesa úr .env skrá
    if ENV_SLOD.exists():
        try:
            with open(ENV_SLOD, "r") as f:
                for lina in f:
                    lina = lina.strip()
                    if lina.startswith("#") or "=" not in lina:
                        continue
                    lykill, _, verdid = lina.partition("=")
                    lykill = lykill.strip()
                    verdid = verdid.strip().strip('"').strip("'")
                    if lykill == nafn:
                        return verdid
        except Exception as villa:
            print(f"⚠️  Villa við lestur .env: {villa}")

    return ""


def fa_api_lykil() -> str:
    """Sækir STRAUMUR_API_KEY úr umhverfi."""
    lykill = lesa_env_breyta("STRAUMUR_API_KEY")
    if not lykill:
        print("❌ STRAUMUR_API_KEY vantar í config/.env")
    return lykill


def fa_terminal_id() -> str:
    """Sækir STRAUMUR_TERMINAL_ID úr umhverfi."""
    terminal = lesa_env_breyta("STRAUMUR_TERMINAL_ID")
    if not terminal:
        print("❌ STRAUMUR_TERMINAL_ID vantar í config/.env")
        print("   → Sækja úr Merchant Portal: Terminals > Select Terminal > Copy Terminal Identifier")
        print("   → Verður að vera 12 stafir")
    return terminal


def fa_hmac_secret() -> str:
    """Sækir STRAUMUR_HMAC_SECRET úr umhverfi."""
    secret = lesa_env_breyta("STRAUMUR_HMAC_SECRET")
    if not secret:
        print("⚠️  STRAUMUR_HMAC_SECRET vantar — webhook HMAC staðfesting óvirk")
    return secret


# =============================================================
# HOSTED CHECKOUT — búa til greiðslulotu
# =============================================================

# --- Búið til úr payment_handler.py (Sprint 76b skipting) ---
