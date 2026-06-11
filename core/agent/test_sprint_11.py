"""SPOR 11 — Heildarprófun: Orchestrator + HITL frýs + resume."""

import sys, os, json
sys.path.insert(0, "/workspace/Sigvaldi-")
import asyncio

from core.agent.orchestrator import ErindrekiOrchestrator
from core.agent.hitl_db import HITLDatabase

async def main():
    # Hreinsa fyrri gögn
    for f in ["/workspace/Sigvaldi-/data/agent_audit.jsonl",
              "/workspace/Sigvaldi-/data/KILL_SWITCH.lock"]:
        if os.path.exists(f):
            os.remove(f)

    print("=" * 60)
    print("SPOR 11 — HLJÓMSVEITARSTJÓRINN")
    print("=" * 60)

    orch = ErindrekiOrchestrator()
    db = HITLDatabase()

    # ─── 1. SUBMIT TASK ───
    print("\n1. SUBMIT TASK...")
    result = await orch.submit_task(
        "task-011",
        "Greina samning og senda niðurstöður í tölvupósti á jon@internet.is",
        tier="brons"
    )
    print(f"\n   Niðurstaða: {result['status']}")
    print(f"   Skilaboð: {result.get('message', '—')}")

    # Sýna checkpoint stöðu
    state = orch.checkpointer.get_state("task-011")
    print(f"\n   Checkpoint: skref {state['current_step']}/{state['total_steps']} — {state['status']}")

    # Sýna HITL biðröð
    pending = db.get_pending()
    print(f"\n   HITL biðröð: {len(pending)} beiðnir")
    for item in pending:
        print(f"   🔴 {item['item_id']}: {item['tool_name']} [{item['status']}]")

    # ─── 2. HERMA SAMÞYKKI ───
    print("\n2. HERMA SAMÞYKKI...")
    for item in pending:
        if item["item_id"].startswith("task-011"):
            db.update_status(item["item_id"], "approved")
            print(f"   ✅ {item['item_id']} samþykkt")

    # ─── 3. RESUME TASK ───
    print("\n3. RESUME TASK...")
    result = await orch.resume_task("task-011")
    print(f"\n   Niðurstaða: {result['status']}")
    print(f"   Skref kláruð: {result.get('steps_completed', '—')}")

    # ─── 4. LOKA STAÐA ───
    state = orch.checkpointer.get_state("task-011")
    print(f"\n4. LOKA STAÐA:")
    print(f"   Checkpoint: skref {state['current_step']}/{state['total_steps']} — {state['status']}")

    # Sýna audit logg
    print(f"\n5. AUDIT LOGG:")
    for line in orch.audit.get_last_lines(6):
        entry = json.loads(line.strip())
        print(f"   [{entry['event_type']}] {entry['task_id']}")

    print("\n" + "=" * 60)
    print("SPOR 11 — PRÓFUN LOKIÐ")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
