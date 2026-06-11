"""Prufuskrift fyrir SPOR 6 — Qwen skipuleggur, HITL stöðvar.

Keyrir alla lykkjuna með alvöru Qwen og sýnir HITL stálgólfið.
"""

import asyncio
import sys
sys.path.insert(0, "/workspace/Sigvaldi-")

from core.agent.llm_local import plan_with_qwen
from core.agent.hitl_queue import ApprovalQueue, HITLInterrupt


async def main():
    print("=" * 60)
    print("SPOR 6 PRUFUSKRIFT — Qwen + HITL")
    print("=" * 60)

    # 1. Qwen skipuleggur
    print("\n1. QWEN SKIPULEGGUR...")
    task = "Greina samning og senda niðurstöður í tölvupósti til jon@internet.is"
    steps = await plan_with_qwen(task)

    if not steps:
        print("❌ Qwen skilaði engri áætlun")
        return

    print(f"   Qwen bjó til {len(steps)} skref:")
    for i, step in enumerate(steps, 1):
        tool = step.get("tool", "?")
        params = step.get("params", {})
        print(f"   {i}. {tool}: {params}")

    # 2. Keyra skrefin — HITL stöðvar send_email
    print("\n2. KEYRI SKREF (HITL STÖÐVAR SEND_EMAIL)...")
    queue = ApprovalQueue()

    for i, step in enumerate(steps, 1):
        tool = step.get("tool", "")
        params = step.get("params", {})

        if tool == "send_email":
            # HITL stálgólf — lykkjan frýs!
            print(f"\n   🔴 SKREF {i}: {tool} — HITL STÖÐVAR!")
            try:
                raise HITLInterrupt(
                    f"hitl-{i:04d}",
                    tool,
                    params,
                )
            except HITLInterrupt as e:
                print(f"   STÖÐVAÐ: {e}")
                queue.submit(
                    e.tool_name,
                    e.params,
                    f"Senda póst til {e.params.get('to', '?')}",
                )
        else:
            print(f"   🟢 SKREF {i}: {tool} — KEYRT BEINT")

    # 3. Sýna biðröð
    print("\n3. BIÐRÖÐ EFTIR LYKKJU:")
    pending = queue.get_pending()
    if pending:
        for item in pending:
            print(f"   🔴 {item.item_id}: {item.tool_name} — {item.preview} [{item.status}]")
    else:
        print("   ✅ Engar óafgreiddar beiðnir")

    # 4. Herma eftir samþykki
    if pending:
        print("\n4. HERMI EFTIR SAMÞYKKI...")
        for item in pending:
            queue.approve(item.item_id)

    # 5. Loka staða
    print("\n5. LOKA STAÐA:")
    all_items = queue.get_all()
    for item in all_items:
        status_icon = "✅" if item.status == "approved" else "❌"
        print(f"   {status_icon} {item.item_id}: {item.tool_name} [{item.status}]")

    print("\n" + "=" * 60)
    print("SPOR 6 PRÓFUN LOKIÐ")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
