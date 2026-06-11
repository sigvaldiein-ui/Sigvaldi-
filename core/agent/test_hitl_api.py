"""Prófar HITL API í einangrun með TestClient — án uvicorn."""

import sys
sys.path.insert(0, "/workspace/Sigvaldi-")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from interfaces.hitl_router import router
from core.agent.hitl_db import HITLDatabase

# Búa til sjálfstætt FastAPI app
app = FastAPI()
app.include_router(router)

client = TestClient(app)
db = HITLDatabase()

print("=" * 60)
print("HITL API PRÓFUN")
print("=" * 60)

# 1. Setja inn prufu-beiðni
print("\n1. Set inn prufu-beiðni...")
db.insert("hitl-0002", "send_email",
          {"to": "jon@internet.is", "subject": "Samninganalýsa", "body": "..."},
          "Senda tölvupóst til jon@internet.is", risk_tier=2)
print("   ✅ Beiðni vistuð")

# 2. GET /api/hitl/queue
print("\n2. GET /api/hitl/queue...")
response = client.get("/api/hitl/queue")
print(f"   HTTP {response.status_code}")
print(f"   JSON: {response.json()}")

# 3. POST /api/hitl/approve/hitl-0002
print("\n3. POST /api/hitl/approve/hitl-0002...")
response = client.post("/api/hitl/approve/hitl-0002")
print(f"   HTTP {response.status_code}")
print(f"   JSON: {response.json()}")

# 4. GET /api/hitl/queue — á að vera tóm núna
print("\n4. GET /api/hitl/queue (á að vera tómt)...")
response = client.get("/api/hitl/queue")
print(f"   HTTP {response.status_code}")
print(f"   JSON: {response.json()}")

# 5. POST /api/hitl/reject/hitl-0003 (sem er ekki til)
print("\n5. POST /api/hitl/reject/hitl-0003 (ekki til)...")
response = client.post("/api/hitl/reject/hitl-0003")
print(f"   HTTP {response.status_code}")
print(f"   JSON: {response.json()}")

print("\n" + "=" * 60)
print("PRÓFUN LOKIÐ")
print("=" * 60)
