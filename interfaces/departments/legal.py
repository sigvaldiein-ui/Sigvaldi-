# interfaces/departments/legal.py
"""Sprint 55 — Legal department specialist."""
from interfaces.departments.base import BaseDepartment


class LegalDepartment(BaseDepartment):
    """Íslenskur lögfræðigreiningasérfræðingur."""

    @property
    def domain(self) -> str:
        return "legal"

    def get_prompt(self, date_str: str = "") -> str:
        prompt = (
            "Þú ert Alvitur, íslenskur lögfræðigreiningasérfræðingur. "
            "Þú hefur þekkingu á íslenskum lögum, reglugerðum og réttarframkvæmd. "
            "Svaraðu nákvæmlega og vísa í viðeigandi lög þar sem við á. "
            "Svaraðu alltaf á íslensku."
        )
        if date_str:
            prompt += f" Dagsetning í dag er {date_str}."
        return prompt
