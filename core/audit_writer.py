"""Sameiginlegur audit-rithöfundur fyrir allt kerfið."""
import os, json
from datetime import datetime, timezone

AUDIT_PATH = "/workspace/Sigvaldi-/audit/alvitur.jsonl"

def _ensure_dir():
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)

def log_query(timestamp: str, user_id: str, tier: str, query: str, domain: str,
              citations_count: int, pipeline_source: str, response: str,
              response_time_ms: float, grounding_ok: bool = None):
    """Skráir fyrirspurn notanda."""
    _ensure_dir()
    entry = {
        "type": "query",
        "timestamp": timestamp,
        "user_id": user_id,
        "tier": tier,
        "query": query,
        "domain": domain,
        "citations_count": citations_count,
        "pipeline_source": pipeline_source,
        "response": response[:500],
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
