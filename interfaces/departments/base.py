# interfaces/departments/base.py
"""
Sprint 55 — Abstract base class fyrir öll departments.

Sérhvert department erfir BaseDepartment og skilgreinir:
  - domain: strengur (t.d. "legal")
  - get_prompt(date_str): skilar system prompt
"""
from abc import ABC, abstractmethod


class BaseDepartment(ABC):
    """Base class fyrir Alvitur departments."""

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain nafn — t.d. 'legal', 'finance'."""
        ...

    @abstractmethod
    def get_prompt(self, date_str: str = "") -> str:
        """
        Skilar specialist system prompt.
        date_str: dagsetning á ISO sniði (t.d. '2026-04-13'), eða tómt.
        """
        ...

    def __repr__(self) -> str:
        return f"<Department domain={self.domain}>"
