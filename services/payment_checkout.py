#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Checkout + greiðslur — úr payment_handler.py"""
from services.payment_config import *

def bua_til_checkout(chat_id: int, plan: str, return_url: str = None) -> dict:
    """
    Býr til Straumur Hosted Checkout lotu.

    Skilar dict með:
      - url: greiðsluslóð (senda í Telegram)
      - checkoutReference: tilvísun til að athuga stöðu
      - villa: villuskilaboð ef eitthvað fór úrskeiðis

    Straumur API: POST /api/v1/hostedcheckout
    Docs: https://docs.straumur.is/hosted-checkout/basic-checkout-request

    Parametrar:
      chat_id    — Telegram notandaauðkenni (notað í reference)
      plan       — Áskriftarplan: 'kynning' | 'einstakling' | 'midgildi'
      return_url — Slóð sem notandi fer á eftir greiðslu (valkvætt)
    """
    if requests is None:
        return {"villa": "requests pakki vantar — pip install requests"}

    # Staðfesta plan
    if plan not in VERDSKRA:
        return {"villa": f"Ógilt plan: '{plan}'. Gildi: {list(VERDSKRA.keys())}"}

    pakki = VERDSKRA[plan]
    if pakki["minor_units"] == 0:
        return {"villa": f"Fyrirtækjapakki er sérsniðinn — hafa samband við Sigvaldi"}

    # Sækja API lykil og terminal
    api_lykill = fa_api_lykil()
    terminal_id = fa_terminal_id()

    if not api_lykill:
        return {"villa": "STRAUMUR_API_KEY vantar"}
    if not terminal_id:
        return {"villa": "STRAUMUR_TERMINAL_ID vantar — sækja úr Merchant Portal"}

    # Búa til einstakt reference (chat_id + tímastimpill + stutt UUID)
    # Þetta gerir auðvelt að tengja greiðslu við notanda
    timi = datetime.now().strftime("%Y%m%d%H%M%S")
    stutt_uuid = uuid.uuid4().hex[:8]
    reference = f"mimir_{chat_id}_{timi}_{stutt_uuid}"

    # Senda beiðni til Straumur
    url = f"{STRAUMUR_BASE_URL}/hostedcheckout"
    headers = {
        "X-API-Key": api_lykill,
        "Content-Type": "application/json",
    }
    payload = {
        "amount": pakki["minor_units"],
        "currency": "ISK",
        "returnUrl": return_url or RETURN_URL,
        "reference": reference,
        "terminalIdentifier": terminal_id,
    }

    try:
        print(f"🔄 Bý til Straumur checkout: {pakki['nafn']} ({pakki['verd_isk']} kr)")
        svar = requests.post(url, json=payload, headers=headers, timeout=30)

        if svar.status_code == 200 or svar.status_code == 201:
            gogn = svar.json()
            print(f"✅ Checkout búinn til: {gogn.get('checkoutReference', '?')}")
            return {
                "url": gogn.get("url", ""),
                "checkoutReference": gogn.get("checkoutReference", ""),
                "responseDateTime": gogn.get("responseDateTime", ""),
                "responseIdentifier": gogn.get("responseIdentifier", ""),
                "reference": reference,
                "plan": plan,
                "chat_id": chat_id,
                "villa": None,
            }
        else:
            villa_texti = f"HTTP {svar.status_code}: {svar.text[:500]}"
            print(f"❌ Straumur villa: {villa_texti}")
            return {"villa": villa_texti}

    except requests.exceptions.Timeout:
        print("❌ Straumur timeout — reyndu aftur")
        return {"villa": "Straumur svaraði ekki (timeout)"}
    except requests.exceptions.ConnectionError as villa:
        print(f"❌ Tengivilla við Straumur: {villa}")
        return {"villa": f"Tengivilla: {villa}"}
    except Exception as villa:
        print(f"❌ Óvænt villa: {villa}")
        return {"villa": f"Óvænt villa: {villa}"}


# =============================================================
# CHECKOUT STATUS — athuga stöðu greiðslu
# =============================================================

def athuga_stodu(checkout_reference: str) -> dict:
    """
    Athugar stöðu Straumur Hosted Checkout lotu.

    Straumur API: GET /api/v1/hostedcheckout/status/{checkoutReference}
    Docs: https://docs.straumur.is/hosted-checkout/hosted-checkout-status

    Möguleg status gildi:
      - "New"       — Lota stofnuð, bíður greiðslu
      - "Completed" — Greiðsla tókst
      - "Expired"   — Lota útrunnin, engin greiðsla

    Skilar dict með status, payfacReference, o.fl.
    """
    if requests is None:
        return {"villa": "requests pakki vantar"}

    api_lykill = fa_api_lykil()
    if not api_lykill:
        return {"villa": "STRAUMUR_API_KEY vantar"}

    url = f"{STRAUMUR_BASE_URL}/hostedcheckout/status/{checkout_reference}"
    headers = {
        "X-API-Key": api_lykill,
    }

    try:
        print(f"🔄 Athuga stöðu: {checkout_reference[:20]}...")
        svar = requests.get(url, headers=headers, timeout=30)

        if svar.status_code == 200:
            gogn = svar.json()
            stada = gogn.get("status", "Unknown")
            print(f"ℹ️  Staða: {stada}")
            return {
                "status": stada,
                "payfacReference": gogn.get("payfacReference"),
                "responseDateTime": gogn.get("responseDateTime", ""),
                "responseIdentifier": gogn.get("responseIdentifier", ""),
                "villa": None,
            }
        else:
            villa_texti = f"HTTP {svar.status_code}: {svar.text[:500]}"
            print(f"❌ Straumur villa: {villa_texti}")
            return {"villa": villa_texti}

    except Exception as villa:
        print(f"❌ Villa við stöðuathugun: {villa}")
        return {"villa": str(villa)}


# =============================================================
# WEBHOOK — meðhöndla tilkynningu frá Straumi
# =============================================================

