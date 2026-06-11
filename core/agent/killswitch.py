"""Kill-Switch — neyðarhemill fyrir Erindrekann."""

import os

LOCK_FILE = "/workspace/Sigvaldi-/data/KILL_SWITCH.lock"


class AgentHaltedException(Exception):
    """Kastast þegar Kill-Switch er virkur."""
    pass


class KillSwitch:
    """Athugar hvort neyðarhemill sé virkur."""

    def __init__(self, lock_path: str = LOCK_FILE):
        self.lock_path = lock_path

    def is_active(self) -> bool:
        """Skilar True ef lock-skrá er til staðar."""
        return os.path.exists(self.lock_path)

    def check(self):
        """Kastar AgentHaltedException ef Kill-Switch er virkur."""
        if self.is_active():
            raise AgentHaltedException("🔴 KILL-SWITCH: Erindrekinn hefur verið stöðvaður!")

    def activate(self):
        """Virkjar Kill-Switch (býr til lock-skrá)."""
        with open(self.lock_path, "w") as f:
            f.write("KILL_SWITCH_ACTIVE")
        print("🔴 KILL-SWITCH VIRKJUR!")

    def deactivate(self):
        """Afvirkjar Kill-Switch (eyðir lock-skrá)."""
        if os.path.exists(self.lock_path):
            os.remove(self.lock_path)
            print("🟢 KILL-SWITCH AFVIRKJUR!")
