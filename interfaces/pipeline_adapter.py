# interfaces/pipeline_adapter.py
"""
Sprint 45 — Production adapter bridging web_server.py to master_pipeline.
Sprint 54 — Orchestrator refactor: sprint39 dependency fjarlægt.

Sprint 39 master_pipeline var upprunalega hannað sem governance lag (policy,
kill-switch, quota, PII, grounding) en kallaði aldrei á LLM í raun — skilað
content = clean_input. Þess vegna fór allt alltaf í fallback path.

Sprint 54: pipeline_adapter skilar alltaf None — fallback path í chat_routes.py
og web_server.py sér um alla LLM vinnslu. Þetta endurspeglar raunveruleikann.

Þessi skrá er geymd til framtíðarnotkunar þegar orchestrator (Sprint 54+)
verður innleiddur með raunverulegri LLM routing.
"""
import logging

logger = logging.getLogger("alvitur.web")


def run_via_pipeline(request_dict: dict) -> dict | None:
    """
    Sprint 54: Pipeline er ekki virkt — skilar alltaf None.
    Fallback path í chat_routes.py sér um LLM vinnslu.

    Þetta er meðvituð hönnunarval: orchestrator verður innleiddur
    í síðari sprint þegar gateway.py og departments eru tilbúin.
    """
    logger.debug(
        "[ALVITUR] pipeline_adapter: skila None — fallback path active "
        "(tier=%s lane=%s)",
        request_dict.get("tier", "?"),
        request_dict.get("lane", "?"),
    )
    return None
