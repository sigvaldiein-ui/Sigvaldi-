"""SPOR 9 — Heildarprófun: Audit, Checkpointer, Kill-Switch."""

import sys
sys.path.insert(0, "/workspace/Sigvaldi-")

from core.agent.audit import AgentAuditLogger
from core.agent.checkpointer import Checkpointer
from core.agent.killswitch import KillSwitch, AgentHaltedException
import json
import os

print("=" * 60)
print("SPOR 9 — AUDIT, CHECKPOINTER, KILL-SWITCH")
print("=" * 60)

# Hreinsa fyrri gögn
for f in ["/workspace/Sigvaldi-/data/agent_audit.jsonl",
          "/workspace/Sigvaldi-/data/KILL_SWITCH.lock"]:
    if os.path.exists(f):
        os.remove(f)

audit = AgentAuditLogger()
checkpointer = Checkpointer()
killswitch = KillSwitch()

task_id = "task-009"
plan_steps = [
    {"tool": "analyze_text", "params": {"text": "Samningur..."}},
    {"tool": "draft_document", "params": {"topic": "Greining"}},
    {"tool": "send_email", "params": {"to": "jon@internet.is"}},
]

# 1. TASK_START
print("\n1. RÆSA VERKEFNI OG AUDIT...")
audit.log_task_start(task_id, "Greina samning og senda póst")
checkpointer.save_state(task_id, json.dumps(plan_steps), 0, len(plan_steps))
print("   ✅ TASK_START loggað + checkpoint vistað")

# 2. KEYRA SKREF 1
print("\n2. KEYRA SKREF 1...")
audit.log_tool_call(task_id, "analyze_text", {"text": "Samningur..."})
checkpointer.save_state(task_id, json.dumps(plan_steps), 1, len(plan_steps))
print("   ✅ Skref 1 klárað, checkpoint uppfært")

# 3. VIRKJA KILL-SWITCH
print("\n3. VIRKJA KILL-SWITCH...")
killswitch.activate()

# 4. REYNA SKREF 2 — Á AÐ STOPPA
print("\n4. REYNA SKREF 2 (á að stoppa)...")
try:
    killswitch.check()
    audit.log_tool_call(task_id, "draft_document", {"topic": "Greining"})
    checkpointer.save_state(task_id, json.dumps(plan_steps), 2, len(plan_steps))
    print("   ❌ SKREF 2 KEYRÐI — KILL-SWITCH VIRKAÐI EKKI!")
except AgentHaltedException as e:
    print(f"   🔴 STOPPAÐ: {e}")
    audit.log_kill_switch(task_id)

# 5. AFTENGJA KILL-SWITCH OG KLÁRA
print("\n5. AFTENGJA KILL-SWITCH OG KLÁRA SKREF 2...")
killswitch.deactivate()
killswitch.check()  # Á ekki að kasta
audit.log_tool_call(task_id, "draft_document", {"topic": "Greining"})
checkpointer.save_state(task_id, json.dumps(plan_steps), 2, len(plan_steps))
audit.log_task_complete(task_id, 2)
print("   ✅ Skref 2 klárað eftir afvirkjun")

# 6. SYNA CHECKPOINT
print("\n6. CHECKPOINTER STAÐA:")
state = checkpointer.get_state(task_id)
print(f"   Task: {state['task_id']}")
print(f"   Skref: {state['current_step']}/{state['total_steps']}")
print(f"   Staða: {state['status']}")

# 7. SYNA AUDIT LOGG
print("\n7. AUDIT LOGG (síðustu línur):")
for line in audit.get_last_lines(8):
    entry = json.loads(line.strip())
    print(f"   [{entry['event_type']}] {entry['task_id']} — {entry['timestamp']}")

print("\n" + "=" * 60)
print("SPOR 9 — PRÓFUN LOKIÐ")
print("=" * 60)
