import sqlite3
import json
from datetime import datetime
import os

class LosslessMemory:
    def __init__(self, db_path="/workspace/mimir_net/data/mimir_memory.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                action TEXT,
                content TEXT,
                metadata TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'guest',
                messages_sent INTEGER DEFAULT 0,
                message_limit INTEGER DEFAULT 5,
                first_seen TEXT
            )
        ''')
        self.conn.commit()

    def log_event(self, agent, action, content, metadata=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log (timestamp, agent_name, action, content, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), agent, action, content, json.dumps(metadata)))
        self.conn.commit()

    def get_or_create_user(self, telegram_id, username="Unknown"):
        cursor = self.conn.cursor()
        cursor.execute("SELECT role, messages_sent, message_limit FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_seen)
                VALUES (?, ?, ?)
            ''', (telegram_id, username, datetime.now().isoformat()))
            self.conn.commit()
            return {"role": "guest", "messages_sent": 0, "message_limit": 5}
        return {"role": user[0], "messages_sent": user[1], "message_limit": user[2]}

    def log_message_and_check_access(self, telegram_id):
        user = self.get_or_create_user(telegram_id)
        if user["role"] in ['admin', 'premium']:
            return True
        if user["messages_sent"] >= user["message_limit"]:
            return False
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET messages_sent = messages_sent + 1 WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
        return True

memory = LosslessMemory()

