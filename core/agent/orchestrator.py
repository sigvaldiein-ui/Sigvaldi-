"""ErindrekiOrchestrator — yfir-klasi sem stýrir öllu flæðinu."""

import json
import sys
sys.path.insert(0, "/workspace/Sigvaldi-")

from core.agent.audit import AgentAuditLogger
from core.agent.checkpointer import Checkpointer
from core.agent.killswitch import KillSwitch, AgentHaltedException
from core.agent.hitl_db import HITLDatabase
from core.agent.llm_router import LLMRouter
from core.agent.hitl_queue import HITLInterrupt
from core.agent.mcp_registry import ToolRegistry, tool_analyze_text, tool_draft_document
from core.agent.mcp_registry import tool_research, tool_send_email, tool_write_code, tool_sign_document


class ErindrekiOrchestrator:
    """Yfir-klasi sem stýrir öllu flæði Erindrekans."""

    def __init__(self):
        self.audit = AgentAuditLogger()
        self.checkpointer = Checkpointer()
        self.killswitch = KillSwitch()
        self.hitl_db = HITLDatabase()
        self.router = LLMRouter()
        self.registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        self.registry.register(tool_analyze_text, description="Greinir texta og dregur út lykilatriði")
        self.registry.register(tool_draft_document, description="Semur drög að skjali")
        self.registry.register(tool_research, description="Rannsakar efni í gegnum Vitann")
        self.registry.register(tool_send_email, description="Sendir tölvupóst", requires_approval=True)
        self.registry.register(tool_write_code, description="Skrifar kóða út frá lýsingu")
        self.registry.register(tool_sign_document, description="Undirritar skjal — HÁ ÁHÆTTA", requires_approval=True)

    async def submit_task(self, task_id: str, description: str, tier: str = "brons") -> dict:
        """Tekur við verkefni, skipuleggur, keyrir skref. Frýs á HITL tólum."""
        print(f"\n{'='*60}")
        print(f"ERINDREKI: {task_id} — {description}")
        print(f"{'='*60}")

        # 1. Audit + Checkpoint start
        self.audit.log_task_start(task_id, description)

        # 2. Velja líkan
        model = self.router.route_task(description, tier)
        print(f"[ORCH] Líkan: {model}")

        # 3. Búa til áætlun (mock fyrir hraða prófun)
        plan_steps = [
            {"tool": "tool_analyze_text", "params": {"text": "Samningur um..."}},
            {"tool": "tool_draft_document", "params": {"topic": "Samninganalýsa", "context": "Greining"}},
            {"tool": "tool_send_email", "params": {"to": "jon@internet.is", "subject": "Niðurstöður", "body": "..."}},
        ]
        total_steps = len(plan_steps)
        self.checkpointer.save_state(task_id, json.dumps(plan_steps), 0, total_steps)
        print(f"[ORCH] Áætlun: {total_steps} skref")

        # 4. Keyra skref
        for i, step in enumerate(plan_steps):
            tool_name = step["tool"]
            params = step["params"]

            # Kill-Switch check
            try:
                self.killswitch.check()
            except AgentHaltedException as e:
                print(f"   🔴 {e}")
                self.audit.log_kill_switch(task_id)
                self.checkpointer.save_state(task_id, json.dumps(plan_steps), i, total_steps, "frozen")
                return {"status": "frozen", "reason": str(e)}

            # HITL check
            if self.registry.requires_approval(tool_name):
                print(f"   🔴 SKREF {i+1}: {tool_name} — HITL STÖÐVAR!")
                self.audit.log_hitl_interrupt(task_id, tool_name, "Krefst samþykkis")
                self.hitl_db.insert(f"{task_id}-{i+1}", tool_name, params,
                                    f"Samþykkis-beiðni: {tool_name}", risk_tier=2)
                self.checkpointer.save_state(task_id, json.dumps(plan_steps), i, total_steps, "frozen")
                return {"status": "frozen", "step": i+1, "tool": tool_name, "message": "Bíður samþykkis"}

            # Keyra tól
            # PII-scrub fail-closed á egress-tólum
            if self.registry.requires_approval(tool_name):
                try:
                    from core.safety.pii_sentry import scrub as pii_scrub
                    for k, v in params.items():
                        if isinstance(v, str):
                            scrubbed = pii_scrub(v)
                            params[k] = scrubbed.scrubbed if hasattr(scrubbed, 'scrubbed') else v
                except Exception as e:
                    print(f"   🔴 PII-scrub villa: {e} — STÖÐVA!")
                    self.audit.log_kill_switch(task_id)
                    return {"status": "frozen", "reason": f"PII-scrub failed: {e}"}
            print(f"   🟢 SKREF {i+1}: {tool_name} — KEYRT")
            self.audit.log_tool_call(task_id, tool_name, params)
            self.checkpointer.save_state(task_id, json.dumps(plan_steps), i+1, total_steps)

        # 5. Klárað
        self.audit.log_task_complete(task_id, total_steps)
        self.checkpointer.save_state(task_id, json.dumps(plan_steps), total_steps, total_steps, "done")
        print(f"[ORCH] {task_id} — ALLT KLÁRAÐ")
        return {"status": "done", "steps_completed": total_steps}

    async def resume_task(self, task_id: str) -> dict:
        """Endurræsir frosið verkefni eftir HITL samþykki."""
        state = self.checkpointer.get_state(task_id)
        if not state:
            return {"status": "error", "message": "Verkefni fannst ekki"}

        if state["status"] != "frozen":
            return {"status": "error", "message": f"Verkefni er {state['status']}, ekki frozen"}

        plan_steps = json.loads(state["plan_json"])
        current_step = state["current_step"]
        total_steps = state["total_steps"]

        print(f"\n[ORCH] Endurræsi {task_id} frá skrefi {current_step+1}/{total_steps}")

        # Athuga HITL samþykki — VERÐUR að vera approved af hitl_router
        import sqlite3
        with sqlite3.connect(self.hitl_db.db_path) as conn:
            rows = conn.execute(
                "SELECT status, approver_sub FROM hitl_queue WHERE item_id LIKE ? || '-%' AND status = 'approved' AND approver_sub != ''",
                (task_id,)
            ).fetchall()
        if not rows:
            print(f"   ⚠️ Ekkert gilt samþykki fyrir {task_id} — get ekki haldið áfram")
            return {"status": "waiting", "message": "Samþykki vantar eða ógilt"}
        print(f"   ✅ Samþykki staðfest fyrir {task_id}")

        # Halda áfram
        self.checkpointer.save_state(task_id, json.dumps(plan_steps), current_step, total_steps, "in_progress")

        for i in range(current_step, len(plan_steps)):
            step = plan_steps[i]
            tool_name = step["tool"]
            params = step["params"]

            try:
                self.killswitch.check()
            except AgentHaltedException as e:
                self.audit.log_kill_switch(task_id)
                self.checkpointer.save_state(task_id, json.dumps(plan_steps), i, total_steps, "frozen")
                return {"status": "frozen", "reason": str(e)}

            # PII-scrub fail-closed á egress-tólum
            if self.registry.requires_approval(tool_name):
                try:
                    from core.safety.pii_sentry import scrub as pii_scrub
                    for k, v in params.items():
                        if isinstance(v, str):
                            scrubbed = pii_scrub(v)
                            params[k] = scrubbed.scrubbed if hasattr(scrubbed, 'scrubbed') else v
                except Exception as e:
                    print(f"   🔴 PII-scrub villa: {e} — STÖÐVA!")
                    self.audit.log_kill_switch(task_id)
                    return {"status": "frozen", "reason": f"PII-scrub failed: {e}"}
            print(f"   🟢 SKREF {i+1}: {tool_name} — KEYRT")
            self.audit.log_tool_call(task_id, tool_name, params)
            self.checkpointer.save_state(task_id, json.dumps(plan_steps), i+1, total_steps)

        self.audit.log_task_complete(task_id, total_steps)
        self.checkpointer.save_state(task_id, json.dumps(plan_steps), total_steps, total_steps, "done")
        print(f"[ORCH] {task_id} — ALLT KLÁRAÐ")
        return {"status": "done", "steps_completed": total_steps - current_step}
