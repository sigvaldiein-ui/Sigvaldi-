"""Dælir sýnigögnum í HITL gagnagrunn fyrir framenda-þróun."""

import sys
sys.path.insert(0, "/workspace/Sigvaldi-")
from core.agent.hitl_db import HITLDatabase

db = HITLDatabase()

print("=" * 50)
print("SÝNIGÖGN FYRIR HITL STJÓRNBORÐ")
print("=" * 50)

# Tier 1 — Lág áhætta (Grænt)
db.insert(
    "mock-0001", "analyze_text",
    {"text": "Stefna félagsins 2026-2028"},
    "Greina stefnuskjal — aðeins innri greining",
    risk_tier=1
)
print("   ✅ Tier 1 (Grænt): analyze_text")

# Tier 2 — Miðlungs áhætta (Gult)
db.insert(
    "mock-0002", "send_email",
    {"to": "jon@internet.is", "subject": "Drög að svari", "body": "Hér eru drög..."},
    "Senda tölvupóst til jon@internet.is með drögum að svari",
    risk_tier=2
)
print("   ✅ Tier 2 (Gult): send_email")

# Tier 3 — Há áhætta (Rautt)
db.insert(
    "mock-0003", "sign_document",
    {"doc_id": "stofnsamningur-ehf-2026", "reason": "Stofnsamningur félags"},
    "UNDIRRITA stofnsamning — RAFRÆN UNDIRRITUN (HÁ ÁHÆTTA)",
    risk_tier=3
)
print("   ✅ Tier 3 (Rautt): sign_document")

# Sýna allt
print(f"\n=== ALLS {len(db.get_pending())} BEIÐNIR Í BIÐRÖÐ ===")
for item in db.get_pending():
    colors = {1: "🟢", 2: "🟡", 3: "🔴"}
    print(f"  {colors.get(item['risk_tier'], '⚪')} {item['item_id']}: {item['tool_name']}")
    print(f"     {item['preview'][:70]}")

print("\n✅ Sýnigögn tilbúin fyrir Hönnuð!")
