#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db_manager.py — Alvitur gagnagrunnsstjóri (Sprint 73 Fasi 3).

Höfundur: Per skv. fyrirmælum Aðals Arkitektsins
SOP: v6.0 — Auðkenni OIDC, sameinuð users tafla, tvöfalt salt.

REGLUR (aldrei breyta):
- Enginn samtalstexti í gagnagrunn — ALDREI
- Aðeins: id, tími, intent, tokens, profiles
- GDPR/Persónuvernd: kennitala alltaf hashed með APP_SALT
- Per-user salt geymt fyrir framtíðar endur-hash
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from interfaces.models.user import hash_kennitala, generate_user_salt

DB_SLOD = Path("/workspace/mimir_net/data/mimir_core.db")


def tengja() -> sqlite3.Connection:
    DB_SLOD.parent.mkdir(parents=True, exist_ok=True)
    tenging = sqlite3.connect(str(DB_SLOD))
    tenging.row_factory = sqlite3.Row
    return tenging


def setja_upp_gagnagrunn() -> None:
    """Setur upp allar töflur — keyrist við ræsingu."""
    with tengja() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                kennitala_hash      TEXT NOT NULL UNIQUE,
                salt                TEXT NOT NULL,
                nafn                TEXT DEFAULT '',
                email               TEXT DEFAULT '',
                straumur_customer_id TEXT,
                subscription_plan   TEXT DEFAULT 'free',
                subscription_end    TEXT,
                free_queries_used   INTEGER DEFAULT 0,
                created_at          TEXT DEFAULT (datetime('now')),
                last_login          TEXT DEFAULT (datetime('now'))
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                intent      TEXT,
                tokens_used INTEGER DEFAULT 0,
                model       TEXT DEFAULT 'unknown',
                created_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id    INTEGER PRIMARY KEY,
                profile_json TEXT DEFAULT '{}',
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        db.commit()


# --- OIDC User operations ---

def finna_eda_bua_til_oidc_user(kennitala: str) -> dict:
    """
    Finnur notanda eftir kennitölu eða býr til nýjan.
    APP_SALT tryggir sama hash fyrir sömu kennitölu.
    Per-user salt geymt fyrir framtíðarþarfir.
    Skilar dict með öllum dálkum.
    """
    kennitala_hash = hash_kennitala(kennitala)

    with tengja() as db:
        row = db.execute(
            "SELECT * FROM users WHERE kennitala_hash = ?",
            (kennitala_hash,)
        ).fetchone()

        if row:
            db.execute(
                "UPDATE users SET last_login = datetime('now') WHERE id = ?",
                (row["id"],)
            )
            db.commit()
            return dict(row)
        else:
            user_salt = generate_user_salt()
            db.execute(
                """INSERT INTO users (kennitala_hash, salt, nafn, email)
                   VALUES (?, ?, '', '')""",
                (kennitala_hash, user_salt)
            )
            db.commit()
            new_row = db.execute(
                "SELECT * FROM users WHERE kennitala_hash = ?",
                (kennitala_hash,)
            ).fetchone()
            return dict(new_row)


def uppfaera_oidc_user(user_id: int, nafn: str = None, email: str = None) -> None:
    """Uppfærir nafn/email eftir innskráningu."""
    with tengja() as db:
        if nafn:
            db.execute("UPDATE users SET nafn = ? WHERE id = ?", (nafn, user_id))
        if email:
            db.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
        db.commit()


# --- Conversation log ---

def skra_samtal(user_id: int, intent: str, tokens_used: int = 0,
                model: str = "unknown") -> int:
    with tengja() as db:
        cursor = db.execute(
            "INSERT INTO conversation_log (user_id, intent, tokens_used, model) VALUES (?, ?, ?, ?)",
            (user_id, intent, tokens_used, model)
        )
        db.commit()
        return cursor.lastrowid


# --- Profile ---

def saekja_profile(user_id: int) -> dict:
    with tengja() as db:
        row = db.execute(
            "SELECT profile_json FROM user_profiles WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row:
            return json.loads(row["profile_json"])
        return {}


def uppfaera_profile(user_id: int, lykilord: str, gildi: str) -> None:
    profile = saekja_profile(user_id)
    profile[lykilord] = gildi
    with tengja() as db:
        db.execute(
            """INSERT INTO user_profiles (user_id, profile_json, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET
               profile_json = excluded.profile_json,
               updated_at = excluded.updated_at""",
            (user_id, json.dumps(profile))
        )
        db.commit()


# --- Health ---

def generate_daily_report() -> str:
    with tengja() as db:
        user_count = db.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
        samtol = db.execute(
            "SELECT COUNT(*) as n FROM conversation_log WHERE date(created_at) = date('now')"
        ).fetchone()["n"]
        tokens = db.execute(
            "SELECT COALESCE(SUM(tokens_used),0) as n FROM conversation_log WHERE date(created_at) = date('now')"
        ).fetchone()["n"]
        return f"Notendur: {user_count} | Samtöl í dag: {samtol} | Tokens í dag: {tokens}"
