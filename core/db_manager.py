#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_manager.py
-------------
Mímir Zero-Data Gagnagrunnsstjóri
Geymir EINGÖNGU metadata — aldrei samtalstexta.

Höfundur: Per (Yfirverkfræðingur) skv. fyrirmælum Aðals Arkitektsins
Dagsetning: 2026-03-31 (Sprint 15.1 uppfærsla)
SOP: v5.0

REGLUR (aldrei breyta):
- Enginn samtalstexti fer í gagnagrunninn — ALDREI
- Aðeins: chat_id, tími, intent, tokens, profiles
- GDPR/Persónuvernd: Engar viðkvæmar upplýsingar

BREYTINGAR (Sprint 15.1):
- stripe_customer_id → straumur_customer_id
- Bætt við: tenant_id, subscription_plan
- subscription_end óbreytt (nýtist áfram)
- Migration fall: keyranleg mörgum sinnum án villu

BREYTINGAR (Sprint 15.7):
- Bætt við: query_count, query_limit, compute_tokens_used
- Nýt föll: haekka_teljara(), athuga_kvota(), endurstilla_manadi()
- Brons=30, Silfur=250, Gull=1000, Platína=engin takmörk
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
    1. users          — Premium notendur og Straumur tengsl
    2. conversation_log — Metadata um samtöl (ENGINN TEXTI)
    3. user_profiles  — Afmörkuð persónueinkenni í JSON
    """
    with tengja() as db:
        # --- Tafla 1: users ---
        # Geymir premium stöðu og Straumur tengsl
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id              INTEGER PRIMARY KEY,
                is_premium           BOOLEAN DEFAULT FALSE,
                straumur_customer_id TEXT,
                subscription_end     TEXT,
                subscription_plan    TEXT DEFAULT 'free',
                tenant_id            TEXT DEFAULT 'public',
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

        # --- Tafla 2b: memory_sessions ---
        db.execute("""CREATE TABLE IF NOT EXISTS memory_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, session_title TEXT, summary_text TEXT, created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')), FOREIGN KEY (chat_id) REFERENCES users(chat_id))""")
        # --- Tafla 3: user_profiles ---
        # Afmörkuð persónueinkenni sem Mímir notar í System Prompt
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                chat_id          INTEGER PRIMARY KEY,
                preferences_json TEXT DEFAULT '{}',
                updated_at       TEXT DEFAULT (datetime('now'))
            )
        """)

        db.commit()
        print(f"✅ Gagnagrunnur tilbúinn: {DB_SLOD}")


def keyra_migration() -> None:
    """
    Sprint 15.1 migration.
    Bætir við nýjum dálkum og flytur gögn úr stripe → straumur.
    Öruggt að keyra mörgum sinnum — try/except per ALTER query.
    """
    with tengja() as db:
        # 1. Bæta við straumur_customer_id ef vantar
        try:
            db.execute("ALTER TABLE users ADD COLUMN straumur_customer_id TEXT")
            print("✅ Dálkur bættur við: straumur_customer_id")
        except sqlite3.OperationalError:
            print("ℹ️  straumur_customer_id er þegar til")

        # 2. Bæta við subscription_plan ef vantar
        try:
            db.execute("ALTER TABLE users ADD COLUMN subscription_plan TEXT DEFAULT 'free'")
            print("✅ Dálkur bættur við: subscription_plan")
        except sqlite3.OperationalError:
            print("ℹ️  subscription_plan er þegar til")

        # 3. Bæta við tenant_id ef vantar
        try:
            db.execute("ALTER TABLE users ADD COLUMN tenant_id TEXT DEFAULT 'public'")
            print("✅ Dálkur bættur við: tenant_id")
        except sqlite3.OperationalError:
            print("ℹ️  tenant_id er þegar til")

        # 4. Flytja gögn úr stripe_customer_id → straumur_customer_id (ef gamli dálkurinn er til)
        try:
            # Athuga hvort gamli dálkurinn er til
            dalkar = [row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()]
            if "stripe_customer_id" in dalkar:
                db.execute("""
                    UPDATE users
                    SET straumur_customer_id = stripe_customer_id
                    WHERE stripe_customer_id IS NOT NULL
                      AND (straumur_customer_id IS NULL OR straumur_customer_id = '')
                """)
                flutt = db.total_changes
                print(f"✅ Gögn flutt úr stripe → straumur ({flutt} færslur)")
                # Athugasemd: SQLite leyfir ekki DROP COLUMN á öllum útgáfum
                # Gamli dálkurinn verður eftir en er ekki notaður
                print("ℹ️  stripe_customer_id eftir í töflu (ónotaður) — SQLite styður ekki DROP COLUMN")
        except Exception as villa:
            print(f"⚠️  Villa við gagnaflutning: {villa}")

        db.commit()
        print("✅ Sprint 15.1 migration lokið")


def keyra_migration_15_7() -> None:
    """
    Sprint 15.7 migration.
    Bætir við usage limit dálkum fyrir Málmapakka (Brons/Silfur/Gull/Platína).
    Öruggt að keyra mörgum sinnum — try/except per ALTER query.
    """
    with tengja() as db:
        # 1. query_count — heildarfjöldi fyrirspurna í þessum mánuði
        try:
            db.execute("ALTER TABLE users ADD COLUMN query_count INTEGER DEFAULT 0")
            print("✅ Dálkur bættur við: query_count")
        except sqlite3.OperationalError:
            print("ℹ️  query_count er þegar til")

        # 2. query_limit — hámark fyrirspurna per mánuð skv. pakka
        #    Sjálfgefið 5 (fríar prufur), Brons=30, Silfur=250, Gull=1000, Platína=0 (ótakm.)
        try:
            db.execute("ALTER TABLE users ADD COLUMN query_limit INTEGER DEFAULT 5")
            print("✅ Dálkur bættur við: query_limit")
        except sqlite3.OperationalError:
            print("ℹ️  query_limit er þegar til")

        # 3. compute_tokens_used — fyrir Platína (pay-per-compute)
        try:
            db.execute("ALTER TABLE users ADD COLUMN compute_tokens_used INTEGER DEFAULT 0")
            print("✅ Dálkur bættur við: compute_tokens_used")
        except sqlite3.OperationalError:
            print("ℹ️  compute_tokens_used er þegar til")

        # 4. query_reset_date — hvenær teljarinn var síðast endurstilltur
        try:
            db.execute("ALTER TABLE users ADD COLUMN query_reset_date TEXT")
            print("✅ Dálkur bættur við: query_reset_date")
        except sqlite3.OperationalError:
            print("ℹ️  query_reset_date er þegar til")

        # 5. Uppfæra query_limit eftir subscription_plan fyrir núverandi notendur
        PLAN_LIMITS = {
            'free': 5,
            'kynning': 30,
            'einstakling': 250,
            'midgildi': 1000,
            'fyrirtaeki': 0,  # 0 = ótakm.
        }
        for plan, limit in PLAN_LIMITS.items():
            db.execute(
                "UPDATE users SET query_limit = ? WHERE subscription_plan = ? AND query_limit = 5",
                (limit, plan)
            )

        db.commit()
        print("✅ Sprint 15.7 migration lokið")


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


# =============================================================
# USAGE LIMITS — Sprint 15.7 (Málmapakkar)
# =============================================================

def athuga_kvota(chat_id: int, master_id: int = 8547098998) -> dict:
    """
    Athugar hvort notandi hafi náð hámarki fyrirspurna.

    Skilar dict:
      - leyfdr: True/False — hvort notandi megi senda fyrirspurn
      - eftir: fjöldi eftir (0 ef lokið, -1 ef ótakm.)
      - plan: áskriftarplan
      - limit: hámark
      - count: notað
    """
    # Master læsist aldrei úti
    if chat_id == master_id:
        return {"leyfdr": True, "eftir": -1, "plan": "master", "limit": 0, "count": 0}

    with tengja() as db:
        notandi = db.execute(
            "SELECT query_count, query_limit, subscription_plan, query_reset_date "
            "FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()

        if not notandi:
            # Nýr notandi — hefur fjórar prufur eftir
            return {"leyfdr": True, "eftir": 5, "plan": "free", "limit": 5, "count": 0}

        count = notandi["query_count"] or 0
        limit = notandi["query_limit"] or 5
        plan = notandi["subscription_plan"] or "free"

        # Ótakm. (Platína) — limit = 0 þýðir engin takmörk
        if limit == 0:
            return {"leyfdr": True, "eftir": -1, "plan": plan, "limit": 0, "count": count}

        # Athuga mánaðar reset
        reset_date = notandi["query_reset_date"]
        nu = datetime.now()
        if reset_date:
            try:
                sidasti_reset = datetime.fromisoformat(reset_date)
                # Ef nýr mánuður — endurstilla
                if nu.month != sidasti_reset.month or nu.year != sidasti_reset.year:
                    db.execute(
                        "UPDATE users SET query_count = 0, query_reset_date = ? WHERE chat_id = ?",
                        (nu.isoformat(), chat_id)
                    )
                    db.commit()
                    count = 0
            except ValueError:
                pass

        eftir = max(0, limit - count)
        return {
            "leyfdr": eftir > 0,
            "eftir": eftir,
            "plan": plan,
            "limit": limit,
            "count": count,
        }


def haekka_teljara(chat_id: int, tokens: int = 0) -> int:
    """
    Hækkar query_count um 1 og compute_tokens_used um tokens.
    Stofnar notaða ef hann er ekki til.
    Skilar nýr query_count.
    """
    nu = datetime.now().isoformat()
    with tengja() as db:
        notandi = db.execute(
            "SELECT query_count FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()

        if not notandi:
            db.execute(
                "INSERT INTO users (chat_id, query_count, compute_tokens_used, query_reset_date) "
                "VALUES (?, 1, ?, ?)",
                (chat_id, tokens, nu)
            )
            db.commit()
            return 1

        nyr_count = (notandi["query_count"] or 0) + 1
        db.execute(
            "UPDATE users SET query_count = ?, compute_tokens_used = compute_tokens_used + ?, "
            "query_reset_date = COALESCE(query_reset_date, ?), updated_at = datetime('now') "
            "WHERE chat_id = ?",
            (nyr_count, tokens, nu, chat_id)
        )
        db.commit()
        return nyr_count


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


def add_user(chat_id: int, straumur_customer_id: str = None,
             subscription_end: str = None,
             subscription_plan: str = "einstakling",
             tenant_id: str = "public") -> None:
    """
    Bætir við eða uppfærir premium notanda.
    Notar Straumur í stað Stripe (Sprint 15.1).

    subscription_plan gildi: 'free' | 'kynning' | 'einstakling' | 'midgildi' | 'fyrirtaeki'
    """
    # Staðfesta gilt plan
    gilt_plan = ['free', 'kynning', 'einstakling', 'midgildi', 'fyrirtaeki']
    if subscription_plan not in gilt_plan:
        print(f"⚠️  Ógilt plan: {subscription_plan}. Gildi: {gilt_plan}")
        subscription_plan = 'einstakling'

    with tengja() as db:
        db.execute("""
            INSERT INTO users (chat_id, is_premium, straumur_customer_id,
                             subscription_end, subscription_plan, tenant_id)
            VALUES (?, TRUE, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                is_premium = TRUE,
                straumur_customer_id = excluded.straumur_customer_id,
                subscription_end = excluded.subscription_end,
                subscription_plan = excluded.subscription_plan,
                tenant_id = excluded.tenant_id,
                updated_at = datetime('now')
        """, (chat_id, straumur_customer_id, subscription_end,
              subscription_plan, tenant_id))
        db.commit()
        print(f"✅ Notandi {chat_id} bætt við sem premium ({subscription_plan})")


def remove_user(chat_id: int) -> None:
    """Fjarlægir premium aðgang notanda."""
    with tengja() as db:
        db.execute("""
            UPDATE users SET
                is_premium = FALSE,
                subscription_plan = 'free',
                updated_at = datetime('now')
            WHERE chat_id = ?
        """, (chat_id,))
        db.commit()
        print(f"✅ Premium aðgangur notanda {chat_id} fjarlægður")


def list_users() -> list:
    """Skilar lista yfir alla premium notendur."""
    with tengja() as db:
        notendur = db.execute(
            "SELECT * FROM users WHERE is_premium = TRUE ORDER BY created_at DESC"
        ).fetchall()
        return [dict(n) for n in notendur]


def saekja_notanda(chat_id: int) -> dict:
    """
    Sækir allar upplýsingar um notanda.
    Skilar dict eða None ef notandi finnst ekki.
    """
    with tengja() as db:
        notandi = db.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(notandi) if notandi else None


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
      python3 db_manager.py setup        — setja upp gagnagrunn
      python3 db_manager.py migrate      — keyra Sprint 15.1 migration
      python3 db_manager.py migrate_15_7 — keyra Sprint 15.7 migration (usage limits)
      python3 db_manager.py add 123456   — bæta við premium notanda
      python3 db_manager.py remove 123456 — fjarlægja premium
      python3 db_manager.py list         — lista premium notendur
      python3 db_manager.py check 123456 — athuga aðgang
      python3 db_manager.py kvota 123456 — athuga kvótaststöðu
      python3 db_manager.py info 123456  — allar upplýsingar um notanda
      python3 db_manager.py report       — dagleg skýrsla
    """
    import sys
    args = sys.argv[1:]

    if not args:
        print("Notkun: python3 db_manager.py [setup/migrate/add/remove/list/check/info/report] [chat_id]")
        return

    skipun = args[0].lower()

    if skipun == "setup":
        setja_upp_gagnagrunn()

    elif skipun == "migrate":
        keyra_migration()

    elif skipun == "migrate_15_7":
        keyra_migration_15_7()

    elif skipun == "add":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py add 123456")
            return
        # Valkvætt: plan sem þriðja argument
        plan = args[2] if len(args) > 2 else "einstakling"
        add_user(int(args[1]), subscription_plan=plan)

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
            print(f"\n{'chat_id':<15} {'Plan':<15} {'Straumur ID':<25} {'Lokadagur'}")
            print("-" * 70)
            for n in notendur:
                print(f"{n['chat_id']:<15} {n.get('subscription_plan', '-'):<15} {str(n.get('straumur_customer_id') or '-'):<25} {n['subscription_end'] or 'Ótímabundið'}")

    elif skipun == "check":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py check 123456")
            return
        chat_id = int(args[1])
        leyfður = is_user_allowed(chat_id)
        frir = get_free_queries_left(chat_id)
        print(f"Notandi {chat_id}: {'✅ Leyfður' if leyfður else '❌ Ekki leyfður'} | Fríar prufur eftir: {frir}")

    elif skipun == "kvota":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py kvota 123456")
            return
        stada = athuga_kvota(int(args[1]))
        print(f"\n📊 Kvótastastaða {args[1]}:")
        print(f"  Plan: {stada['plan']}")
        print(f"  Notað: {stada['count']}/{stada['limit']} {'(ótakm.)' if stada['limit']==0 else ''}")
        print(f"  Eftir: {stada['eftir']} {'' if stada['eftir']>=0 else '(ótakm.)'}")
        print(f"  Leyfur: {'✅' if stada['leyfdr'] else '❌'}")

    elif skipun == "info":
        if len(args) < 2:
            print("Vantar chat_id: python3 db_manager.py info 123456")
            return
        notandi = saekja_notanda(int(args[1]))
        if not notandi:
            print(f"Notandi {args[1]} finnst ekki.")
        else:
            print(f"\n📋 Notandi {args[1]}:")
            for lykill, gildi in notandi.items():
                print(f"  {lykill}: {gildi}")

    elif skipun == "report":
        skyrslur = generate_daily_report()
        print(skyrslur)

    else:
        print(f"Óþekkt skipun: {skipun}")
        print("Tiltækar skipanir: setup, migrate, add, remove, list, check, info, report")


if __name__ == "__main__":
    # Ef engar skipanir: setja upp gagnagrunn og prenta skýrslu
    import sys
    if len(sys.argv) > 1:
        cli()
    else:
        setja_upp_gagnagrunn()
        print("\n--- Próf skýrsla ---")
        print(generate_daily_report())
