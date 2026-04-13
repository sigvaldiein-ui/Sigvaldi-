# interfaces/departments/research.py
"""Sprint 55 — Research department specialist."""
from interfaces.departments.base import BaseDepartment


class ResearchDepartment(BaseDepartment):
    """Íslenskur rannsóknarsérfræðingur."""

    @property
    def domain(self) -> str:
        return "research"

    def get_prompt(self, date_str: str = "") -> str:
        prompt = (
            "Þú ert Alvitur, íslenskur rannsóknarsérfræðingur. "
            "Þú greinir gögn, dregur saman niðurstöður og gefur faglegar skýringar. "
            "Svaraðu með skipulögðum hætti og vísa í heimildir þar sem við á. "
            "Svaraðu alltaf á íslensku."
        )
        if date_str:
            prompt += f" Dagsetning í dag er {date_str}."
        return prompt
