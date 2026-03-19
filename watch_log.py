import time
import requests

TOKEN = "8581446527:AAGE3qlY1DRF2JVpIPF5uWohd2YtoN8N1uo"
CHAT_ID = "8547098998"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

last_size = 0
while True:
    with open("/workspace/mimir.log") as f:
        lines = f.readlines()
    errors = [l for l in lines if "Error" in l or "Exception" in l or "409" in l]
    if errors:
        send_alert(f"⚠️ Mímir villa:\n{errors[-1]}")
    time.sleep(60)
