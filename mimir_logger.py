import json, os
from datetime import datetime

LOG_FILE = "/workspace/conversations.jsonl"

def log_conversation(user_id, user_msg, bot_reply):
    entry = {"ts": str(datetime.now()), "user_id": user_id, "user": user_msg, "bot": bot_reply}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
