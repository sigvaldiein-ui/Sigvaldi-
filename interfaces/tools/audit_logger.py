"""Sprint 97.7 — SecureAuditLogger með SQLite backing [status: persistent]."""
import hashlib
import time
import aiosqlite

class SecureAuditLogger:
    def __init__(self):
        self.last_hash = "0" * 64

    async def load_last_hash(self, db_path: str = "state_store.db"):
        """Restart-safe: sækir síðasta hash úr gagnagrunni."""
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_chain (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    jti TEXT,
                    user_sub TEXT,
                    tool_name TEXT,
                    action TEXT,
                    prev_hash TEXT,
                    this_hash TEXT
                )
            """)
            await db.commit()
            async with db.execute("SELECT this_hash FROM audit_chain ORDER BY seq DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    self.last_hash = row[0]

    async def log_action(self, jti: str, user_sub: str, tool_name: str, action: str, db_path: str = "state_store.db") -> str:
        timestamp = time.time()
        payload = f"{self.last_hash}|{timestamp}|{jti}|{user_sub}|{tool_name}|{action}"
        new_hash = hashlib.sha256(payload.encode()).hexdigest()
        prev_hash = self.last_hash
        self.last_hash = new_hash
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                INSERT INTO audit_chain (timestamp, jti, user_sub, tool_name, action, prev_hash, this_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, jti, user_sub, tool_name, action, prev_hash, new_hash))
            await db.commit()
        return new_hash
