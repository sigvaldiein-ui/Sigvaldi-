import subprocess, time, requests

TOKEN = "8581446527:AAGE3qlY1DRF2JVpIPF5uWohd2YtoN8N1uo"
ADMIN_CHAT_ID = "8547098998"
LOG = "/workspace/mimir.log"

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": ADMIN_CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def is_running(name):
    r = subprocess.run(["pgrep", "-f", name], capture_output=True)
    return r.returncode == 0

def start_mimir():
    subprocess.Popen(["python", "/workspace/mimir_bot.py"], stdout=open(LOG, "a"), stderr=open(LOG, "a"))
    time.sleep(3)

def check_log_for_errors():
    try:
        with open(LOG, "r") as f:
            lines = f.readlines()[-20:]
        return [l for l in lines if "Error" in l or "409" in l]
    except:
        return []

send_telegram("Mimir Agent Core raestur!")
crash_count = 0

while True:
    if not is_running("mimir_bot.py"):
        crash_count += 1
        send_telegram(f"Mimir fell! Endurraesi #{crash_count}")
        start_mimir()
        if is_running("mimir_bot.py"):
            send_telegram("Mimir er aftur vakinn!")
        else:
            send_telegram("Mimir raestist ekki!")
    errors = check_log_for_errors()
    if len(errors) >= 3:
        send_telegram(f"Villur: {errors[-1]}")
    time.sleep(30)
