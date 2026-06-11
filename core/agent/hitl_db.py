"""HITL gagnagrunnur — SQLite varanleg geymsla fyrir samþykkis-biðröð."""

import sqlite3
import json
import os
from typing import List, Optional
from datetime import datetime, timezone

DB_PATH = "/workspace/Sigvaldi-/data/hitl_queue.db"


class HITLDatabase:
    """Varanleg geymsla fyrir HITL beiðnir."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_table()

    def _init_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hitl_queue (
                    item_id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    params TEXT NOT NULL,
                    preview TEXT NOT NULL,
                    risk_tier INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    decided_at TEXT
                )
            """)
            conn.commit()

    def insert(self, item_id: str, tool_name: str, params: dict, 
               preview: str, risk_tier: int = 1) -> bool:
        """Vista nýja beiðni."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO hitl_queue (item_id, tool_name, params, preview, risk_tier, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                    (item_id, tool_name, json.dumps(params), preview, risk_tier,
                     datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
            print(f"[DB] Vistaði: {item_id}")
            return True
        except sqlite3.IntegrityError:
            print(f"[DB] Villa: {item_id} er þegar til")
            return False

    def get_pending(self) -> List[dict]:
        """Sækja allar óafgreiddar beiðnir."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM hitl_queue WHERE status = 'pending' ORDER BY created_at"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, item_id: str, status: str) -> bool:
        """Uppfæra stöðu beiðni."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE hitl_queue SET status = ?, decided_at = ? WHERE item_id = ? AND status = 'pending'",
                (status, datetime.now(timezone.utc).isoformat(), item_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                print(f"[DB] {item_id} → {status}")
                return True
            print(f"[DB] {item_id} fannst ekki eða þegar afgreidd")
            return False


if __name__ == "__main__":
    db = HITLDatabase()
    db.insert("hitl-test", "send_email", {"to": "test@test.is"}, "Test beiðni")
    print("Pending:", db.get_pending())
    db.update_status("hitl-test", "approved")
    print("Pending eftir:", db.get_pending())
