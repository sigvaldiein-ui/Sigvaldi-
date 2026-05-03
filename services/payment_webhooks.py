#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Webhook + HMAC vinnsla — úr payment_handler.py"""
from services.payment_config import *
from services.payment_checkout import *

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
