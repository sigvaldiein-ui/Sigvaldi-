import subprocess, time, os, sys

print("=== 1. STAÐFESTA NÝJAN KÓÐA ===")
os.chdir("/workspace/Sigvaldi-")
patterns = ["_get_search_context CALLED", "search_web returned n_citations"]
for p in patterns:
    r = subprocess.run(["grep", "-n", p, "interfaces/chat_routes.py"], capture_output=True, text=True)
    print(r.stdout.strip() or f"EKKI FUNDIÐ: {p}")

print("\n=== 2. DREPA ÖLL UVICORN FERLI ===")
subprocess.run(["pkill", "-9", "-f", "uvicorn"], capture_output=True)
time.sleep(3)
r = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True)
if r.stdout.strip():
    print("VIÐVÖRUN: Enn uvicorn ferli í gangi!")
    sys.exit(1)
print("Öll uvicorn ferli dauð.")

print("\n=== 3. HREINSA ALLAN CACHE ===")
subprocess.run(["find", "/workspace", "-name", "*.pyc", "-delete"], capture_output=True)
subprocess.run(["find", "/workspace", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], capture_output=True)
print("Cache hreinsaður.")

print("\n=== 4. RÆSA UVICORN ===")
logfile = "/workspace/web_server_clean.log"
with open(logfile, "w") as log:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.Popen(
        ["python3", "-m", "uvicorn", "interfaces.web_server:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=log, stderr=log, env=env
    )
time.sleep(8)

# Staðfesta að uvicorn sé lifandi
r = subprocess.run(["pgrep", "-f", "uvicorn"], capture_output=True, text=True)
if not r.stdout.strip():
    print("VIÐVÖRUN: Uvicorn ræstist ekki!")
    sys.exit(1)
print("Uvicorn lifandi.")

print("\n=== 5. CURL PRÓFUN ===")
r = subprocess.run(["curl", "-sS", "-X", "POST", "http://127.0.0.1:8000/api/chat",
                    "-H", "Content-Type: application/json",
                    "-d", '{"query":"stjórnarskrá"}'], capture_output=True, text=True)
print(r.stdout.strip()[:500])

print("\n=== 6. [80c] LOGGAR ===")
time.sleep(2)
r = subprocess.run(["grep", "-E", "80c:", logfile], capture_output=True, text=True)
print(r.stdout.strip() or "Engar [80c] línur í loggi - athugaðu handvirkt með: grep 80c: /workspace/web_server_clean.log")

print("\nDAGUR LOKIÐ.")
