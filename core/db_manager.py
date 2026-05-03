"""Gagnagrunnsstjórnun — tengingar, töflur, analytics (Sprint 74 F3: user-föll → services/)."""
import sqlite3
import os
import logging

logger = logging.getLogger("alvitur.db")

# --- Stillingar ---
_GAGNAGRUNNS_SKRA = os.getenv("ALVITUR_DB_PATH", "/workspace/Sigvaldi-/data/alvitur.db")


def tengja() -> sqlite3.Connection:
    """Skilar SQLite tengingu með row_factory stilltri."""
    conn = sqlite3.connect(_GAGNAGRUNNS_SKRA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def setja_upp_gagnagrunn() -> None:
    """Býr til töflur — keyrt við ræsingu."""
    conn = tengja()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kennitala_hash TEXT NOT NULL UNIQUE,
                nafn TEXT,
                email TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                búinn_til TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sidast_breytt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS samtalsaga (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                intent TEXT,
                tokens_used INTEGER DEFAULT 0,
                model TEXT DEFAULT 'unknown',
                fyrirspurn TEXT,
                timi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_users_kennitala ON users(kennitala_hash);
            CREATE INDEX IF NOT EXISTS idx_samtalsaga_user ON samtalsaga(user_id);
            CREATE INDEX IF NOT EXISTS idx_samtalsaga_timi ON samtalsaga(timi);
        """)
        conn.commit()
        logger.info("Gagnagrunnstöflur staðfestar.")
    except Exception as e:
        logger.error(f"Villa við uppsetningu gagnagrunns: {e}")
        raise
    finally:
        conn.close()


# --- Analytics & Reporting ---

def skra_samtal(user_id: int, intent: str, tokens_used: int = 0,
                 model: str = "unknown", fyrirspurn: str = "") -> None:
    """Skráir samtal í gagnagrunn — analytics."""
    conn = tengja()
    try:
        conn.execute(
            "INSERT INTO samtalsaga (user_id, intent, tokens_used, model, fyrirspurn, timi) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (user_id, intent, tokens_used, model, fyrirspurn),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Villa við skráningu samtals: {e}")
    finally:
        conn.close()




# --- Audit Log (Sprint 79) ---

def skra_audit(
    user_id: int | None = None,
    action: str = "UNKNOWN",
    tier: str = "general",
    query_text: str | None = None,
    response_text: str | None = None,
    tokens_used: int = 0,
    model: str = "unknown",
    pipeline_source: str | None = None,
    rag_chunks_count: int = 0,
    client_ip: str | None = None,
    success: bool = True,
    error_code: str | None = None,
    metadata: str = "{}",
) -> None:
    """Skráir atburð í audit_log_v2 (mimir_memory.db)."""
    import hashlib

    query_hash = hashlib.sha256((query_text or "").encode()).hexdigest()[:16] if query_text else None
    response_hash = hashlib.sha256((response_text or "").encode()).hexdigest()[:16] if response_text else None
    client_ip_hash = hashlib.sha256((client_ip or "").encode()).hexdigest()[:16] if client_ip else None

    try:
        conn = sqlite3.connect("/workspace/Sigvaldi-/data/mimir_memory.db")
        conn.execute(
            """INSERT INTO audit_log_v2 
               (user_id, action, tier, query_hash, response_hash, tokens_used, model, pipeline_source, rag_chunks_count, client_ip_hash, success, error_code, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, action, tier, query_hash, response_hash, tokens_used, model, pipeline_source, rag_chunks_count, client_ip_hash, success, error_code, metadata),
        )
        conn.commit()
        logger.debug(f"[AUDIT] {action} skráð — user={user_id} success={success}")
    except Exception as e:
        logger.warning(f"[AUDIT] Villa við skráningu: {e}")
    finally:
        conn.close()


def generate_daily_report() -> str:
    """Býr til daglega samantekt — admin."""
    conn = tengja()
    try:
        cur = conn.execute(
            "SELECT COUNT(*) as samtol, SUM(tokens_used) as tokens "
            "FROM samtalsaga WHERE date(timi) = date('now')"
        )
        row = cur.fetchone()
        samtol = row["samtol"] or 0
        tokens = row["tokens"] or 0
        return f"Dags: {samtol} samtöl, {tokens} tokens."
    except Exception as e:
        logger.error(f"Villa við daglega skýrslu: {e}")
        return "Villa við að sækja skýrslu."
    finally:
        conn.close()
