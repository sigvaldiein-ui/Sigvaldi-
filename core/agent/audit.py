"""G-AUDIT — JSONL loggun fyrir AI Act fylgni."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

AUDIT_PATH = "/workspace/Sigvaldi-/data/agent_audit.jsonl"


class AgentAuditLogger:
    """Skráir allar aðgerðir Erindrekans í JSONL format."""

    def __init__(self, path: str = AUDIT_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def log(self, event_type: str, task_id: str, details: Optional[dict] = None):
        """Skráir einn atburð."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "task_id": task_id,
            "details": details or {},
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_task_start(self, task_id: str, description: str):
        self.log("TASK_START", task_id, {"description": description})

    def log_llm_call(self, task_id: str, model: str, tokens: int = 0, cost: float = 0.0):
        self.log("LLM_CALL", task_id, {"model": model, "tokens": tokens, "cost_usd": cost})

    def log_tool_call(self, task_id: str, tool_name: str, params: dict):
        self.log("TOOL_CALL", task_id, {"tool": tool_name, "params": params})

    def log_hitl_interrupt(self, task_id: str, tool_name: str, reason: str):
        self.log("HITL_INTERRUPT", task_id, {"tool": tool_name, "reason": reason})

    def log_task_complete(self, task_id: str, steps: int):
        self.log("TASK_COMPLETE", task_id, {"steps_completed": steps})

    def log_kill_switch(self, task_id: str):
        self.log("KILL_SWITCH", task_id, {"reason": "Agent halted by kill-switch"})

    def get_last_lines(self, n: int = 5) -> list:
        """Sækir síðustu n línur úr audit skránni."""
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-n:] if len(lines) >= n else lines
