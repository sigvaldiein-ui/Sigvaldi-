# interfaces/specialist_prompts.py
"""
Sprint 47 — Domain routing + specialist prompts.
Sprint 53a — Switched to Qwen3.5-27B (ekki-US) fyrir classify.
Sprint 53b — Nota config.py fyrir módel stillingar.
Sprint 55 — Nota departments package.
Sprint 56 — Nota ClassifySkill í stað beinna LLM kalla.

classify() les fyrstu 500 stafi og skilar einu af: legal, finance, writing, research, general.
get_specialist_prompt() sækir prompt úr viðeigandi department.
"""
import logging
from interfaces.skills.classify import ClassifySkill as _ClassifySkill

logger = logging.getLogger("alvitur.web")

DOMAINS = ["legal", "finance", "writing", "research", "general"]

_classify_skill = _ClassifySkill()


async def classify(text: str) -> str:
    """
    Flokkar fyrstu 500 stafi af text í domain.
    Sprint 56: Notar ClassifySkill.
    Skilar: domain strengur — fallback 'general'
    """
    return await _classify_skill.run(text=text)


def get_specialist_prompt(domain: str, date_str: str = "") -> str:
    """
    Skilar specialist system prompt fyrir gefið domain.
    Sprint 55: Sækir prompt úr departments package.
    """
    from interfaces.departments import get_department
    dept = get_department(domain)
    return dept.get_prompt(date_str)
