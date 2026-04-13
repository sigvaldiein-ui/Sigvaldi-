# interfaces/departments/general.py
"""Sprint 55 — General department (fallback)."""
from interfaces.departments.base import BaseDepartment


class GeneralDepartment(BaseDepartment):
    """Almennt íslenskt AI assistant — fallback fyrir óþekkt domain."""

    @property
    def domain(self) -> str:
        return "general"

    def get_prompt(self, date_str: str = "") -> str:
        prompt = (
            "Þú ert Alvitur, íslenskur AI aðstoðarmaður. "
            "Svaraðu skýrt og hnitmiðað. "
            "Svaraðu alltaf á íslensku."
        )
        if date_str:
            prompt += f" Dagsetning í dag er {date_str}."
        return prompt
