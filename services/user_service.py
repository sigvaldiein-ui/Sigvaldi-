"""User service — einangrar notendaaðgerðir frá db_manager (Sprint 74 Fasi 3)."""
import logging
from typing import Optional

from core.db_manager import tengja
from interfaces.models.user import hash_kennitala

logger = logging.getLogger("alvitur.services.user")


def finna_eda_bua_til_oidc_user(kennitala: str) -> dict:
    """Finnur eða býr til notanda út frá kennitölu. Skilar dict með id, kennitala_hash, role."""
    conn = tengja()
    kt_hashed = hash_kennitala(kennitala)
    
    cur = conn.execute(
        "SELECT id, kennitala_hash, nafn, email, role FROM users WHERE kennitala_hash = ?",
        (kt_hashed,),
    )
    row = cur.fetchone()
    
    if row:
        logger.info(f"Notandi fannst: user_id={row['id']}")
        return {
            "id": row["id"],
            "kennitala_hash": row["kennitala_hash"],
            "nafn": row["nafn"],
            "email": row["email"],
            "role": row["role"],
            "is_new": False,
        }
    
    cur = conn.execute(
        "INSERT INTO users (kennitala_hash, role) VALUES (?, ?)",
        (kt_hashed, "user"),
    )
    conn.commit()
    user_id = cur.lastrowid
    logger.info(f"Nýr notandi búinn til: user_id={user_id}")
    
    return {
        "id": user_id,
        "kennitala_hash": kt_hashed,
        "nafn": None,
        "email": None,
        "role": "user",
        "is_new": True,
    }


def uppfaera_oidc_user(user_id: int, nafn: Optional[str] = None, email: Optional[str] = None) -> None:
    """Uppfærir nafn og/eða email OIDC notanda."""
    conn = tengja()
    if nafn:
        conn.execute("UPDATE users SET nafn = ? WHERE id = ?", (nafn, user_id))
    if email:
        conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    conn.commit()
    logger.info(f"Notandi uppfærður: user_id={user_id}")


def saekja_profile(user_id: int) -> dict:
    """Sækir prófíl notanda."""
    conn = tengja()
    cur = conn.execute(
        "SELECT id, nafn, email, role FROM users WHERE id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Notandi fannst ekki: user_id={user_id}")
    return {
        "id": row["id"],
        "nafn": row["nafn"],
        "email": row["email"],
        "role": row["role"],
    }


def uppfaera_profile(user_id: int, lykilord: str, gildi: str) -> None:
    """Uppfærir prófílreit notanda (takmarkað við örugga reiti)."""
    leyfdir_reitir = {"nafn", "email"}
    if lykilord not in leyfdir_reitir:
        raise ValueError(f"Óleyfilegur reitur: {lykilord}")
    
    conn = tengja()
    conn.execute(f"UPDATE users SET {lykilord} = ? WHERE id = ?", (gildi, user_id))
    conn.commit()
    logger.info(f"Prófíll uppfærður: user_id={user_id}, {lykilord}={gildi}")
