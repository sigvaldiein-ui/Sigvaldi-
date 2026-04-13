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

def reikna_hmac(payload: dict, hmac_secret: str) -> str:
    """
    Reiknar HMAC-SHA256 undirskrift skv. Straumur forskrift.
    Docs: https://docs.straumur.is/webhooks/payment/hmac-validation

    Röðin er:
    CheckoutReference:PayfacReference:MerchantReference:Amount:Currency:Reason:Success

    Skilar base64-kóðaðri undirskrift.
    """
    # Sækja gildi í réttri röð (tómt ef vantar)
    gildi = [
        payload.get("checkoutReference", "") or "",
        payload.get("payfacReference", "") or "",
        payload.get("merchantReference", "") or "",
        payload.get("amount", "") or "",
        payload.get("currency", "") or "",
        payload.get("reason", "") or "",
        payload.get("success", "") or "",
    ]

    # Sameina með ':'
    skilaboð = ":".join(gildi)

    # Breyta hex secret í bytes
    try:
        hex_secret = hmac_secret
        if len(hex_secret) % 2 == 1:
            hex_secret += "0"
        lykill_bytes = bytes.fromhex(hex_secret)
    except ValueError as villa:
        print(f"⚠️  Villa við hex umbreytingu á HMAC secret: {villa}")
        return ""

    # Reikna HMAC-SHA256
    skilaboð_bytes = skilaboð.encode("utf-8")
    hmac_obj = hmac.new(lykill_bytes, skilaboð_bytes, hashlib.sha256)

    import base64
    return base64.b64encode(hmac_obj.digest()).decode("utf-8")


def stadfesta_hmac(payload: dict) -> bool:
    """
    Staðfestir HMAC undirskrift á webhook frá Straumi.
    Skilar True ef undirskrift er rétt, False annars.
    """
    hmac_secret = fa_hmac_secret()
    if not hmac_secret:
        # Ef enginn secret → leyfa (en vara við)
        print("⚠️  HMAC secret vantar — sleppi staðfestingu (EKKI gera í PROD)")
        return True

    undirskrift_fra_straumi = payload.get("hmacSignature", "")
    if not undirskrift_fra_straumi:
        print("⚠️  Webhook vantar hmacSignature")
        return False

    reiknuð = reikna_hmac(payload, hmac_secret)

    if hmac.compare_digest(undirskrift_fra_straumi, reiknuð):
        print("✅ HMAC undirskrift staðfest")
        return True
    else:
        print("❌ HMAC undirskrift stenst EKKI")
        return False


def vinna_ur_webhook(payload: dict) -> dict:
    """
    Vinnur úr webhook tilkynningu frá Straumi.
    Docs: https://docs.straumur.is/webhooks/payment/authorization-event

    Flæðið:
    1. Staðfesta HMAC undirskrift
    2. Athuga hvort greiðsla tókst (success == "true")
    3. Greina reference til að finna chat_id og plan
    4. Uppfæra gagnagrunn (is_premium, straumur_customer_id, o.fl.)
    5. Skila niðurstöðu

    Webhook payload dæmi:
    {
        "checkoutReference": "...",
        "payfacReference": "OOJWITWVQV42PSE8",
        "merchantReference": "mimir_12345_20260331120000_abc12345",
        "amount": "199000",
        "currency": "ISK",
        "reason": "383528:1111:03/2030",
        "success": "true",
        "hmacSignature": "...",
        "additionalData": {
            "eventType": "Authorization",
            ...
        }
    }

    Skilar dict:
      - adgerd: hvað var gert
      - chat_id: notandi sem greiddi
      - plan: áskriftarplan
      - villa: ef eitthvað fór úrskeiðis
    """
    print("📨 Webhook móttekin frá Straumi")

    # 1. Staðfesta HMAC
    if not stadfesta_hmac(payload):
        return {"villa": "HMAC staðfesting mistókst", "adgerd": "hafnað"}

    # 2. Athuga event type
    additional = payload.get("additionalData", {})
    event_type = additional.get("eventType", "Unknown")
    success = payload.get("success", "false")

    print(f"ℹ️  Event: {event_type}, Success: {success}")

    if event_type != "Authorization":
        print(f"ℹ️  Sleppi event type: {event_type} (aðeins Authorization er meðhöndlað)")
        return {"adgerd": "sleppt", "event_type": event_type, "villa": None}

    if success != "true":
        print(f"⚠️  Greiðsla mistókst: reason={payload.get('reason', '?')}")
        return {
            "adgerd": "greiðsla_mistókst",
            "reason": payload.get("reason", ""),
            "villa": "Greiðsla mistókst",
        }

    # 3. Greina reference til að finna chat_id og plan
    # Reference snið: mimir_{chat_id}_{timestamp}_{uuid}
    merchant_ref = payload.get("merchantReference", "")
    chat_id = None
    plan = None

    if merchant_ref and merchant_ref.startswith("mimir_"):
        hlutar = merchant_ref.split("_")
        if len(hlutar) >= 3:
            try:
                chat_id = int(hlutar[1])
            except ValueError:
                print(f"⚠️  Gat ekki lesið chat_id úr reference: {merchant_ref}")

    if not chat_id:
        print(f"⚠️  Chat_id vantar í reference: {merchant_ref}")
        return {
            "adgerd": "villa",
            "villa": f"Chat_id vantar í reference: {merchant_ref}",
        }

    # 4. Finna plan út frá upphæð
    upphæð = int(payload.get("amount", "0"))
    for plan_nafn, upplysingar in VERDSKRA.items():
        if upplysingar["minor_units"] == upphæð:
            plan = plan_nafn
            break

    if not plan:
        # Ef upphæð passar ekki neitt plan — nota einstakling sem default
        print(f"⚠️  Upphæð {upphæð} passar ekkert plan — nota 'einstakling'")
        plan = "einstakling"

    # 5. Uppfæra gagnagrunn
    pakki = VERDSKRA[plan]
    lokadagur = (datetime.now() + timedelta(days=pakki["timi_dagar"])).isoformat()
    payfac_ref = payload.get("payfacReference", "")

    try:
        # Reyna að importa db_manager
        import sys
        sys.path.insert(0, "/workspace/mimir_net/core")
        from db_manager import add_user
        add_user(
            chat_id=chat_id,
            straumur_customer_id=payfac_ref,
            subscription_end=lokadagur,
            subscription_plan=plan,
        )
        print(f"✅ Notandi {chat_id} uppfærður: {plan} til {lokadagur[:10]}")
        return {
            "adgerd": "premium_virkjað",
            "chat_id": chat_id,
            "plan": plan,
            "lokadagur": lokadagur,
            "payfacReference": payfac_ref,
            "villa": None,
        }
    except ImportError:
        print("⚠️  Gat ekki importað db_manager — uppfærsla frálögð")
        return {
            "adgerd": "db_villa",
            "chat_id": chat_id,
            "plan": plan,
            "villa": "Gat ekki importað db_manager",
        }
    except Exception as villa:
        print(f"❌ Villa við uppfærslu gagnagrunns: {villa}")
        return {
            "adgerd": "db_villa",
            "chat_id": chat_id,
            "plan": plan,
            "villa": str(villa),
        }


# =============================================================
# HJÁLPARFÖLL — fyrir Telegram bot
# =============================================================

def fa_verdskra_texta() -> str:
    """
    Skilar fallegum Markdown texta með verðskrá.
    Notað í Telegram til að sýna notanda áskriftarmöguleika.
    """
    texti = "💰 **Áskriftarleiðir Mímis:**\n\n"
    for plan_id, pakki in VERDSKRA.items():
        if pakki["verd_isk"] == 0:
            texti += f"🏢 **{pakki['nafn']}** — Sérsett verð\n"
        else:
            texti += f"{'💎' if plan_id == 'midgildi' else '⭐'} **{pakki['nafn']}** — {pakki['verd_isk']:,} kr/mán\n"
    texti += "\n📩 Veldu pakka til að hefja áskrift."
    return texti


def fa_plan_upplysingar(plan: str) -> dict:
    """Skilar upplýsingum um tiltekið plan eða None."""
    return VERDSKRA.get(plan)


# =============================================================
# CLI — Command Line Interface
# =============================================================

def cli():
    """
    Stjórnlínutól til að prófa payment_handler.

    Dæmi:
      python3 payment_handler.py verdskra              — sýna verðskrá
      python3 payment_handler.py checkout 12345 kynning — búa til checkout
      python3 payment_handler.py stada <ref>            — athuga stöðu
      python3 payment_handler.py webhook_test           — prófa webhook meðhöndlun
      python3 payment_handler.py env                    — athuga umhverfisbreytur
    """
    import sys
    args = sys.argv[1:]

    if not args:
        print("Notkun: python3 payment_handler.py [verdskra|checkout|stada|webhook_test|env]")
        print("  verdskra              — sýna verðskrá")
        print("  checkout <chat_id> <plan> — búa til checkout lotu")
        print("  stada <checkoutReference>  — athuga stöðu")
        print("  webhook_test          — prófa webhook meðhöndlun (hermd gögn)")
        print("  env                   — athuga umhverfisbreytur")
        return

    skipun = args[0].lower()

    if skipun == "verdskra":
        print(fa_verdskra_texta())

    elif skipun == "checkout":
        if len(args) < 3:
            print("Vantar: python3 payment_handler.py checkout <chat_id> <plan>")
            print(f"  Gildi plan: {list(VERDSKRA.keys())}")
            return
        chat_id = int(args[1])
        plan = args[2]
        nidurstada = bua_til_checkout(chat_id, plan)
        if nidurstada.get("villa"):
            print(f"❌ Villa: {nidurstada['villa']}")
        else:
            print(f"\n✅ Checkout tilbúinn!")
            print(f"   URL: {nidurstada['url']}")
            print(f"   Reference: {nidurstada['checkoutReference']}")
            print(f"   Okkar ref: {nidurstada['reference']}")

    elif skipun == "stada":
        if len(args) < 2:
            print("Vantar: python3 payment_handler.py stada <checkoutReference>")
            return
        nidurstada = athuga_stodu(args[1])
        if nidurstada.get("villa"):
            print(f"❌ Villa: {nidurstada['villa']}")
        else:
            print(f"\n📋 Staða: {nidurstada['status']}")
            if nidurstada.get("payfacReference"):
                print(f"   PayfacRef: {nidurstada['payfacReference']}")

    elif skipun == "webhook_test":
        print("🧪 Prófa webhook meðhöndlun (hermd gögn)...")
        # Hermd webhook gögn
        hermd_payload = {
            "checkoutReference": "test_abc123def456",
            "payfacReference": "TESTPAY001",
            "merchantReference": "mimir_8547098998_20260331120000_test1234",
            "amount": "199000",
            "currency": "ISK",
            "reason": "383528:1111:03/2030",
            "success": "true",
            "hmacSignature": "",  # Tómt — HMAC sleppt ef secret vantar
            "additionalData": {
                "eventType": "Authorization",
                "authCode": "123456",
                "cardSummary": "1111",
                "paymentMethod": "VI",
            },
        }
        nidurstada = vinna_ur_webhook(hermd_payload)
        print(f"\n📋 Niðurstaða: {json.dumps(nidurstada, indent=2, ensure_ascii=False)}")

    elif skipun == "env":
        print("🔍 Athuga umhverfisbreytur...")
        api = fa_api_lykil()
        terminal = fa_terminal_id()
        hmac_s = fa_hmac_secret()
        print(f"  STRAUMUR_API_KEY:      {'✅ Fundinn' if api else '❌ Vantar'}")
        print(f"  STRAUMUR_TERMINAL_ID:  {'✅ Fundinn (' + terminal[:4] + '...)' if terminal else '❌ Vantar'}")
        print(f"  STRAUMUR_HMAC_SECRET:  {'✅ Fundinn' if hmac_s else '⚠️  Vantar (webhook HMAC óvirkt)'}")
        print(f"\n  BASE_URL: {STRAUMUR_BASE_URL}")
        print(f"  .env slóð: {ENV_SLOD}")

    else:
        print(f"Óþekkt skipun: {skipun}")
        print("Tiltækar skipanir: verdskra, checkout, stada, webhook_test, env")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cli()
    else:
        # Sjálfgefið: sýna verðskrá og athuga umhverfi
        print("=== Payment Handler — Straumur ===\n")
        print(fa_verdskra_texta())
        print("\n--- Umhverfi ---")
        api = fa_api_lykil()
        terminal = fa_terminal_id()
        print(f"  API Key:     {'✅' if api else '❌'}")
        print(f"  Terminal ID: {'✅' if terminal else '❌'}")
        print(f"  Base URL:    {STRAUMUR_BASE_URL}")
