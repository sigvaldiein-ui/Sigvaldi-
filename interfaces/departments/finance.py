# interfaces/departments/finance.py
"""Sprint 55 — Finance department specialist."""
from interfaces.departments.base import BaseDepartment


class FinanceDepartment(BaseDepartment):
    """Íslenskur fjármálagreiningasérfræðingur."""

    @property
    def domain(self) -> str:
        return "finance"

    def get_prompt(self, date_str: str = "") -> str:
        prompt = (
            "Þú ert Alvitur, íslenskur fjármálagreiningasérfræðingur. "
            "Þú hefur þekkingu á reikningsskilum, fjárfestingum og fjármálamálum. "
            "Svaraðu með tölulegar upplýsingar þar sem við á og skýrðu hugtök. "
            "Svaraðu alltaf á íslensku."
        )
        if date_str:
            prompt += f" Dagsetning í dag er {date_str}."
        return prompt
