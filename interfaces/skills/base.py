# interfaces/skills/base.py
"""
Sprint 56 — Abstract base class fyrir öll skills.

Sérhvert skill útfærir:
  - name: strengur (t.d. "classify", "translate")
  - run(**kwargs): async aðal fall — skilar niðurstöðu
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """Base class fyrir Alvitur skills."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill nafn — t.d. 'classify', 'translate'."""
        ...

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """
        Keyrir skill með gefnum arguments.
        Sérhvert skill skilgreinir sín eigin kwargs.
        Graceful degradation: ef villa kemur upp skal skila fallback gildi.
        """
        ...

    def __repr__(self) -> str:
        return f"<Skill name={self.name}>"
