"""Sameiginlegur audit-rithöfundur fyrir allt kerfið."""
import os, json
from datetime import datetime, timezone

AUDIT_PATH = "/workspace/Sigvaldi-/audit/alvitur.jsonl"

def _ensure_dir():
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)

def log_query(timestamp: str, user_id: str, tier: str, query: str, domain: str,
              citations_count: int, pipeline_source: str, response: str,
              response_time_ms: float, grounding_ok: bool = None,
              actions_logged: str = "", observations: dict = None,
              search_context_len: int = 0):
    """Skráir fyrirspurn notanda — sameinað snið."""
    _ensure_dir()
    entry = {
        "type": "query",
        "timestamp": timestamp,
        "user_id": user_id,
        "tier": tier,
        "query": query[:200],
        "domain": domain,
        "actions_logged": actions_logged,
        "observations": observations or {},
        "response": response[:500],
        "search_context_len": search_context_len,
        "citations_count": citations_count,
        "pipeline_source": pipeline_source,
        "response_time_ms": round(response_time_ms, 2),
        "grounding_ok": grounding_ok
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))

def log_hitl(item_id: str, decision: str, approver_sub: str):
    """Skráir HITL samþykki eða höfnun."""
    _ensure_dir()
    entry = {
        "type": "hitl_decision",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "item_id": item_id,
        "decision": decision,
        "approver_sub": approver_sub
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))

def log_egress(tool_name, params, task_id, approver_sub="", status="executed"):
    """Egress-adgerd i sameinada slod. Geymir EKKI innihald params - adeins lykla."""
    _ensure_dir()
    entry = {
        "type": "egress",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "tool_name": tool_name,
        "approver_sub": approver_sub,
        "status": status,
        "param_keys": sorted(list(params.keys())) if isinstance(params, dict) else []
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))
