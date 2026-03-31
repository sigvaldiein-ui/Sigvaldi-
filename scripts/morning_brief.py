#!/usr/bin/env python3
import os, sys, requests, sqlite3
from datetime import datetime, timedelta
sys.path.append('/workspace/mimir_net')
from dotenv import load_dotenv
load_dotenv('/workspace/mimir_net/config/.env')

DB_SLOD = '/workspace/mimir_net/data/mimir_core.db'
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
CHAT_ID = 8547098998

def saekja_tolur():
    nu = datetime.now()
    fyrir_24 = nu - timedelta(hours=24)
    try:
        db = sqlite3.connect(DB_SLOD)
        db.row_factory = sqlite3.Row
        heild = db.execute("SELECT COUNT(*) as f FROM conversation_log WHERE timestamp >= ?", (fyrir_24.isoformat(),)).fetchone()['f']
        notendur = db.execute("SELECT COUNT(DISTINCT chat_id) as f FROM conversation_log WHERE timestamp >= ?", (fyrir_24.isoformat(),)).fetchone()['f']
        premium = db.execute("SELECT COUNT(*) as f FROM users WHERE is_premium = TRUE").fetchone()['f']
        tokens = db.execute("SELECT SUM(tokens_used) as s FROM conversation_log WHERE timestamp >= ?", (fyrir_24.isoformat(),)).fetchone()['s'] or 0
        skipting = db.execute("SELECT intent, COUNT(*) as f FROM conversation_log WHERE timestamp >= ? GROUP BY intent ORDER BY f DESC", (fyrir_24.isoformat(),)).fetchall()
        db.close()
        return heild, notendur, premium, tokens, skipting
    except Exception as e:
        return 0, 0, 0, 0, []

def smida_skyrslur(heild, notendur, premium, tokens, skipting):
    MANUDAIR = ["januar","februar","mars","april","mai","juni","juli","agust","september","oktober","november","desember"]
    nu = datetime.now()
    dags = f"{nu.day}. {MANUDAIR[nu.month-1]} {nu.year}"
    linar = [
        f"Godan daginn Forstjori!",
        f"Dagsetning: {dags}",
        f"",
        f"Tolur sidastu 24 klst:",
        f"Samtol: {heild}",
        f"Einstakir notendur: {notendur}",
        f"Premium notendur: {premium}",
        f"Tokens notadur: {tokens:,}",
    ]
    if skipting:
        linar.append("")
        linar.append("Skipting samtala:")
        for row in skipting:
            emoji = {"SEARCH":"🔍","CHAT":"💬","FILE":"📎"}.get(row['intent'],"❓")
            linar.append(f"{emoji} {row['intent']}: {row['f']}")
    if heild == 0:
        linar.append("")
        linar.append("Engin samtol i gaer - kerfid i hvild.")
    linar.append("")
    linar.append("Mimir v7.1 Omni-Mind")
    return "\n".join(linar)

def senda_telegram(texti):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": texti}, timeout=15)
        if r.status_code == 200:
            print("Sent!")
            return True
        else:
            print(f"Villa: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"Villa: {e}")
        return False

if __name__ == "__main__":
    print("Sendi morgunskyrslur a Sigvalda...")
    heild, notendur, premium, tokens, skipting = saekja_tolur()
    skyrslur = smida_skyrslur(heild, notendur, premium, tokens, skipting)
    senda_telegram(skyrslur)
