# interfaces/departments/writing.py
"""Sprint 55 — Writing department specialist."""
from interfaces.departments.base import BaseDepartment


class WritingDepartment(BaseDepartment):
    """Íslenskur ritstjóri og textavinnslusérfræðingur."""

    @property
    def domain(self) -> str:
        return "writing"

    def get_prompt(self, date_str: str = "") -> str:
        prompt = (
            "Þú ert Alvitur, íslenskur ritstjóri og textavinnslusérfræðingur. "
            "Þú hjálpar við ritun, endurskoðun og umbætur á texta. "
            "Svaraðu með skýrum tillögum og útskýringum. "
            "Svaraðu alltaf á íslensku."
        )
        if date_str:
            prompt += f" Dagsetning í dag er {date_str}."
        return prompt
