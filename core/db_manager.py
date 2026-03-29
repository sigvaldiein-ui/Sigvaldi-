#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_manager.py
-------------
Mímir Zero-Data Gagnagrunnsstjóri
Geymir EINGÖNGU metadata — aldrei samtalstexta.

Höfundur: Per (Yfirverkfræðingur) skv. fyrirmælum Aðals Arkitektsins
Dagsetning: 2026-03-29
SOP: v5.0

REGLUR (aldrei breyta):
- Enginn samtalstexti fer í gagnagrunninn — ALDREI
- Aðeins: chat_id, tími, intent, tokens, profiles
- GDPR/Persónuvernd: Engar viðkvæmar upplýsingar
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# --- Stillingar ---
# Algild slóð að gagnagrunni
DB_SLOD = Path("/workspace/mimir_net/data/mimir_core.db")


def tengja() -> sqlite3.Connection:
    """
    Tengist SQLite gagnagrunni.
    Búar til hann ef hann er ekki til.
    Skilar connection hlut.
    """
    # Tryggja að mappa sé til
    DB_SLOD.parent.mkdir(parents=True, exist_ok=True)

    tenging = sqlite3.connect(str(DB_SLOD))
    # Skilgreinir dálkaheiti í niðurstöðum
    tenging.row_factory = sqlite3.Row
    return tenging


def setja_upp_gagnagrunn() -> None:
    """
    Setur upp allar töflur í gagnagrunni ef þær eru ekki til.
    Keyrist einu sinni við ræsingu.

    Þrjár töflur skv. SOP v5.0:
    1. users          — Premium notendur og Stripe tengsl
    2. conversation_log — Metadata um samtöl (ENGINN TEXTI)
    3. user_profiles  — Afmörkuð persónueinkenni í JSON
    """
    with tengja() as db:
        # --- Tafla 1: users ---
        # Geymir premium stöðu og Stripe tengsl
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id              INTEGER PRIMARY KEY,
                is_premium           BOOLEAN DEFAULT FALSE,
                stripe_customer_id   TEXT,
                subscription_end     TEXT,
                free_queries_used    INTEGER DEFAULT 0,
                created_at           TEXT DEFAULT (datetime('now')),
                updated_at           TEXT DEFAULT (datetime('now'))
            )
        """)

        # --- Tafla 2: conversation_log ---
        # EINGÖNGU metadata — enginn texti úr samtalinu
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id      INTEGER NOT NULL,
                timestamp    TEXT DEFAULT (datetime('now')),
                intent       TEXT CHECK(intent IN ('SEARCH', 'CHAT', 'FILE', 'UNKNOWN')),
                tokens_used  INTEGER DEFAULT 0,
                response_ms  INTEGER DEFAULT 0
            )
        """)

        # --- Tafla 3: user_profiles ---
        # Afmörkuð persónueinkenni sem Mímir notar í System Prompt
        # Dæmi: {"nafn": "Sigvaldi", "titill": "Forstjóri", "stilll": "Faglegur"}
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                chat_id          INTEGER PRIMARY KEY,
                preferences_json TEXT DEFAULT '{}',
                updated_at       TEXT DEFAULT (datetime('now'))
            )
        """)

        db.commit()
        print(f"✅ Gagnagrunnur tilbúinn: {DB_SLOD}")


# =============================================================
# USERS — hjálparföll
# =============================================================

def is_user_allowed(chat_id: int, master_id: int = 8547098998) -> bool:
    """
    Athugar hvort notandi hafi aðgang.
    Master ID (Sigvaldi) hefur alltaf aðgang.
    Premium notendur með virka áskrift hafa aðgang.
    Óþekktir notendur fá aðgang ef þeir hafa fríar prufur eftir.
    """
    # Master ID læsist aldrei úti
    if chat_id == master_id:
        return True

    with tengja() as db:
        notandi = db.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()

        if not notandi:
            return False

        # Athuga premium stöðu
        if notandi["is_premium"]:
            # Athuga hvort áskrift sé enn í gildi
            if notandi["subscription_end"]:
                lokadagur = datetime.fromisoformat(notandi["subscription_end"])
                if datetime.now() < lokadagur:
                    return True
            else:
                return True

        return False


def get_free_queries_left(chat_id: int) -> int:
    """Skilar fjölda frírra prufna sem eru eftir (0-5)."""
    MAX_FRITT = 5
    with tengja() as db:
        notandi = db.execute(
            "SELECT free_queries_used FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()

        if not notandi:
            return MAX_FRITT

        notadar = notandi["free_queries_used"] or 0
        return max(0, MAX_FRITT - notadar)


def nota_frja_prufu(chat_id: int) -> int:
    """
    Telur niður eina fría prufu.
    Stofnar notanda ef hann er ekki til.
    Skilar fjölda prufna sem eru eftir.
    """
    MAX_FRITT = 5
    with tengja() as db:
        notandi = db.execute(
            "SELECT free_queries_used FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()

        if not notandi:
            # Stofna nýjan notanda
            db.execute(
                "INSERT INTO users (chat_id, free_queries_used) VALUES (?, 1)",
                (chat_id,)
            )
            db.commit()
            return MAX_FRITT - 1
        else:
            notadar = (notandi["free_queries_used"] or 0) + 1
            db.execute(
                "UPDATE users SET free_queries_used = ?, updated_at = datetime('now') WHERE chat_id = ?",
                (notadar, chat_id)
            )
            db.commit()
            return max(0, MAX_FRITT - notadar)


def add_user(chat_id: int, stripe_customer_id: str = None,
             subscription_end: str = None) -> None:
    """Bætir við eða uppfærir premium notanda."""
    with tengja() as db:
        db.execute("""
            INSERT INTO users (chat_id, is_premium, stripe_customer_id, subscription_end)
            VALUES (?, TRUE, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                is_premium = TRUE,
                stripe_customer_id = excluded.stripe_customer_id,
                subscription_end = excluded.subscription_end,
                updated_at = datetime('now')
        """, (chat_id, stripe_customer_id, subscription_end))
        db.commit()
        print(f"✅ Notandi {chat_id} bætt við sem premium")


def remove_user(chat_id: int) -> None:
    """Fjarlægir premium aðgang notanda."""
    with tengja() as db:
        db.execute(
            "UPDATE users SET is_premium = FALSE, updated_at = datetime('now') WHERE chat_id = ?",
            (chat_id,)
        )
        db.commit()
        print(f"✅ Premium aðgangur notanda {chat_id} fjarlægður")


def list_users() -> list:
    """Skilar lista yfir alla premium notendur."""
    with tengja() as db:
        notendur = db.execute(
            "SELECT * FROM users WHERE is_premium = TRUE ORDER BY created_at DESC"
        ).fetchall()
        return [dict(n) for n in notendur]


# =============================================================
# CONVERSATION LOG — hjálparföll
# =============================================================

def skra_samtal(chat_id: int, intent: str, tokens_used: int = 0,
                response_ms: int = 0) -> None:
    """
    Skráir metadata um eitt samtal.
    ENGINN TEXTI — aðeins tölulegar upplýsingar og flokkun.

    chat_id    — Telegram notandaauðkenni
    intent     — SEARCH / CHAT / FILE / UNKNOWN
    tokens_used — Áætlaður fjöldi tokens
    response_ms — Svartími í millisekúndum
    """
    # Tryggja gilt intent gildi
    gilt_intent = ["SEARCH", "CHAT", "FILE", "UNKNOWN"]
    if intent not in gilt_intent:
        intent = "UNKNOWN"

    with tengja() as db:
        db.execute("""
            INSERT INTO conversation_log (chat_id, intent, tokens_used, response_ms)
            VALUES (?, ?, ?, ?)
        """, (chat_id, intent, tokens_used, response_ms))
        db.commit()


# =============================================================
# USER PROFILES — hjálparföll
# =============================================================

def saekja_profile(chat_id: int) -> dict:
    """
    Sækir persónueinkenni notanda.
    Skilar tómum dict ef ekkert er skráð.
    """
    with tengja() as db:
        profile = db.execute(
            "SELECT preferences_json FROM user_profiles WHERE chat_id = ?",
            (chat_id,)
        ).fetchone()

        if not profile:
            return {}

        try:
            return json.loads(profile["preferences_json"])
        except json.JSONDecodeError:
            return {}


def uppfaera_profile(chat_id: int, lykilord: str, gildi: str) -> None:
    """
    Uppfærir eitt persónueinkenni notanda.
    Dæmi: uppfaera_profile(123, "nafn", "Sigvaldi")
    """
    with tengja() as db:
        # Sækja núverandi profile
        profile = saekja_profile(chat_id)
        profile[lykilord] = gildi

        profile_json = json.dumps(profile, ensure_ascii=False)

        db.execute("""
            INSERT INTO user_profiles (chat_id, preferences_json)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                preferences_json = excluded.preferences_json,
                updated_at = datetime('now')
        """, (chat_id, profile_json))
        db.commit()


# =============================================================
# DAGLEG SKÝRSLA — CEO Morning Brief
# =============================================================

def generate_daily_report() -> str:
    """
    Greinir conversation_log fyrir síðustu 24 klst.
    Skilar fallegum Markdown texta sem sendur er í Telegram.

    Format:
    🌅 Góðan daginn Forstjóri
    📊 Tölur síðustu 24 klst...
    """
    nu = datetime.now()
    fyrir_24 = nu - timedelta(hours=24)
    MANUDAIR = ["janúar","febrúar","mars","apríl","maí","júní",
                "júlí","ágúst","september","október","nóvember","desember"]
    dagsetning = f"{nu.day}. {MANUDAIR[nu.month-1]} {nu.year}"

    with tengja() as db:
        # Heildarfjöldi samtala
        heild = db.execute("""
            SELECT COUNT(*) as fjoldi FROM conversation_log
            WHERE timestamp >= ?
        """, (fyrir_24.isoformat(),)).fetchone()["fjoldi"]

        # Skipting eftir intent
        skipting = db.execute("""
            SELECT intent, COUNT(*) as fjoldi FROM conversation_log
            WHERE timestamp >= ?
            GROUP BY intent ORDER BY fjoldi DESC
        """, (fyrir_24.isoformat(),)).fetchall()

        # Fjöldi einstakra notenda
        notendur = db.execute("""
            SELECT COUNT(DISTINCT chat_id) as fjoldi FROM conversation_log
            WHERE timestamp >= ?
        """, (fyrir_24.isoformat(),)).fetchone()["fjoldi"]

        # Heildarfjöldi tokens
        tokens = db.execute("""
            SELECT SUM(tokens_used) as heild FROM conversation_log
            WHERE timestamp >= ?
        """, (fyrir_24.isoformat(),)).fetchone()["heild"] or 0

        # Meðal svartími
        medal_ms = db.execute("""
            SELECT AVG(response_ms) as medal FROM conversation_log
            WHERE timestamp >= ? AND response_ms > 0
        """, (fyrir_24.isoformat(),)).fetchone()["medal"] or 0

        # Premium notendur
        premium = db.execute(
            "SELECT COUNT(*) as fjoldi FROM users WHERE is_premium = TRUE"
        ).fetchone()["fjoldi"]

    # Smíða skýrsluna
    skyrslur = [f"🌅 **Góðan daginn Forstjóri!**\n📅 {dagsetning}\n"]
    skyrslur.append("📊 **Tölur síðustu 24 klst:**")
    skyrslur.append(f"• Samtöl: **{heild}**")
    skyrslur.append(f"• Einstakir notendur: **{notendur}**")
    skyrslur.append(f"• Premium notendur: **{premium}**")
    skyrslur.append(f"• Tokens notaðir: **{tokens:,}**")

    if medal_ms > 0:
        skyrslur.append(f"• Meðal svartími: **{medal_ms/1000:.1f} sek**")

    if skipting:
        skyrslur.append("\n🧠 **Skipting samtala:**")
        for row in skipting:
            emoji = {"SEARCH": "🔍", "CHAT": "💬", "FILE": "📎"}.get(row["intent"], "❓")
            skyrslur.append(f"• {emoji} {row['intent']}: {row['fjoldi']}")

    if heild == 0:
        skyrslur.append("\n😴 Engin samtöl í gær — kerfið í hvíld.")

    skyrslur.append("\n🤖 _Mímir v7.1 Omni-Mind_")

    return "\n".join(skyrslur)


# =============================================================
# CLI — Command Line Interface
# =============================================================

def cli():
    """
    Stjórnlínutól fyrir Sigvalda.
    Keyrsla: python3 db_manager.py [skipun] [chat_id]

    Dæmi:
      python3 db_manager.py add 123456
      python3 db_manager.py remove 123456
      python3 db_manager.py list
      python3 db_manager.py check 123456
      python3 db_manager.py report
      python3 db_manager.py setup
    """
    import sys
    args = sys.argv[1:]

    if not args:
        print("Notkun: python3 db_manager.py [add/remove/list/check/report/setup] [chat_id]")
        return

    skipun = args[0].lower()

    if skipun == "setup":
        setja_upp_gagnagrunn()

    elif skipun == "add":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py add 123456")
            return
        add_user(int(args[1]))

    elif skipun == "remove":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py remove 123456")
            return
        remove_user(int(args[1]))

    elif skipun == "list":
        notendur = list_users()
        if not notendur:
            print("Engir premium notendur skráðir.")
        else:
            print(f"\n{'chat_id':<15} {'Premium':<10} {'Stripe ID':<30} {'Lokadagur'}")
            print("-" * 70)
            for n in notendur:
                print(f"{n['chat_id']:<15} {'✅':<10} {str(n['stripe_customer_id'] or '-'):<30} {n['subscription_end'] or 'Ótímabundið'}")

    elif skipun == "check":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py check 123456")
            return
        chat_id = int(args[1])
        leyfður = is_user_allowed(chat_id)
        frir = get_free_queries_left(chat_id)
        print(f"Notandi {chat_id}: {'✅ Leyfður' if leyfður else '❌ Ekki leyfður'} | Fríar prufur eftir: {frir}")

    elif skipun == "report":
        skyrslur = generate_daily_report()
        print(skyrslur)

    else:
        print(f"Óþekkt skipun: {skipun}")
        print("Tiltækar skipanir: add, remove, list, check, report, setup")


if __name__ == "__main__":
    # Ef engar skipanir: setja upp gagnagrunn og prenta skýrslu
    import sys
    if len(sys.argv) > 1:
        cli()
    else:
        setja_upp_gagnagrunn()
        print("\n--- Próf skýrsla ---")
        print(generate_daily_report())
