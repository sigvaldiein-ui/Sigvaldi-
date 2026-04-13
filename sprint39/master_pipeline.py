"""Sprint 39 — Master Pipeline (LEGACY).

Sprint 54: Þessi skrá er sett í legacy stöðu.

Upprunalega hönnun (Sprint 39): governance lag með policy engine, kill-switch,
quota enforcement, PII detection, task classification, LLM gateway routing og
grounding pipeline. Þetta kerfi kallaði aldrei á LLM í raun — skilað
content = clean_input — og fór þess vegna alltaf í fallback.

Sprint 54: pipeline_adapter.py skilar alltaf None. Allur LLM kóði er í:
  - interfaces/chat_routes.py  (/api/chat)
  - interfaces/web_server.py   (/api/analyze-document)

Orchestrator verður endurhannaður í Sprint 55+ með:
  - gateway.py (úr config.py)
  - departments/
  - skills/
"""


def run_request(request_dict: dict) -> dict:
    """Legacy — ekki notað í production. Sjá pipeline_adapter.py."""
    return {
        "error": True,
        "message": "master_pipeline er í legacy stöðu. Sjá pipeline_adapter.py.",
    }
