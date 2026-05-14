import subprocess, time, os

print("=== 1. STAÐFESTA NÝJAN KÓÐA ===")
os.chdir("/workspace/Sigvaldi-")

patterns = ["_get_search_context CALLED", "search_web returned n_citations"]
for p in patterns:
    r = subprocess.run(["grep", "-n", p, "interfaces/chat_routes.py"], capture_output=True, text=True)
    print(r.stdout.strip() or f"EKKI FUNDIÐ: {p}")

print("\n=== 2. DREPA GAMLA UVICORN ===")
subprocess.run(["pkill", "-9", "-f", "uvicorn"])
time.sleep(3)

print("=== 3. HREINSA CACHE ===")
subprocess.run(["find", "/workspace", "-name", "*.pyc", "-delete"])
subprocess.run(["find", "/workspace", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"])

print("=== 4. RÆSA NÝJAN UVICORN ===")
with open("/workspace/web_server_clean.log", "w") as log:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.Popen(
        ["python3", "-m", "uvicorn", "interfaces.web_server:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=log, stderr=log, env=env
    )
time.sleep(5)

print("=== 5. CURL PRÓFUN ===")
r = subprocess.run(["curl", "-sS", "-X", "POST", "http://127.0.0.1:8000/api/chat",
                    "-H", "Content-Type: application/json",
                    "-d", '{"query":"stjórnarskrá"}'], capture_output=True, text=True)
print(r.stdout.strip()[:500])

time.sleep(2)

print("\n=== 6. [80c] LOGGAR ===")
r = subprocess.run(["grep", "-E", "80c:", "/workspace/web_server_clean.log"], capture_output=True, text=True)
print(r.stdout.strip() or "Engar [80c] línur í loggi")

print("\nDAGUR LOKIÐ.")
