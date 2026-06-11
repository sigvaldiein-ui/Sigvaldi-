"""Checkpointer — varðveitir stöðu AgentLoop í SQLite."""

import sqlite3
import json
import os
from typing import Optional

DB_PATH = "/workspace/Sigvaldi-/data/agent_state.db"


class Checkpointer:
    """Geymir og endurheimtir stöðu Agent-lykkju."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_table()

    def _init_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    task_id TEXT PRIMARY KEY,
                    plan_json TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'in_progress',
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_state(self, task_id: str, plan_json: str, current_step: int, 
                   total_steps: int, status: str = "in_progress"):
        """Vistar núverandi stöðu."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agent_state 
                   (task_id, plan_json, current_step, total_steps, status, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (task_id, plan_json, current_step, total_steps, status, now)
            )
            conn.commit()
        print(f"[CHECKPOINT] Vistað: {task_id} — skref {current_step}/{total_steps}")

    def load_state(self, task_id: str) -> Optional[dict]:
        """Endurheimtir stöðu verkefnis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM agent_state WHERE task_id = ?", (task_id,)
            ).fetchone()
        if row:
            print(f"[CHECKPOINT] Endurheimt: {task_id} — skref {row['current_step']}/{row['total_steps']}")
            return dict(row)
        print(f"[CHECKPOINT] Ekkert fannst fyrir: {task_id}")
        return None

    def get_state(self, task_id: str) -> Optional[dict]:
        """Sækir stöðu án þess að prenta."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM agent_state WHERE task_id = ?", (task_id,)
            ).fetchone()
        return dict(row) if row else None
