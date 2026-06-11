"""HITL Samþykkis-biðröð — stálgólf Erindrekans.

Öll tól sem eru merkt requires_approval=True VERÐA að fara í gegnum
þessa biðröð. Lykkjan frýs þar til samþykki berst.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class HITLInterrupt(Exception):
    """Sérstök undantekning sem frýs Agent lykkjuna.

    Þegar Executor rekst á tól sem krefst samþykkis,
    kastar hann þessari undantekningu. Lykkjan frýs.
    """

    def __init__(self, item_id: str, tool_name: str, params: Dict[str, Any]):
        self.item_id = item_id
        self.tool_name = tool_name
        self.params = params
        super().__init__(
            f"HITL stöðvaði '{tool_name}'. Beiðni {item_id} bíður samþykkis."
        )


class ApprovalItem:
    """Ein samþykkis-beiðni í biðröðinni."""

    def __init__(
        self,
        item_id: str,
        tool_name: str,
        params: Dict[str, Any],
        preview: str,
        risk_tier: int = 1,
    ):
        self.item_id = item_id
        self.tool_name = tool_name
        self.params = params
        self.preview = preview
        self.risk_tier = risk_tier
        self.status = "pending"  # pending, approved, rejected
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.decided_at: Optional[str] = None


class ApprovalQueue:
    """Samþykkis-biðröð — HITL stálgólfið.

    Geymir beiðnir þar til notandi samþykkir eða hafnar.
    """

    def __init__(self):
        self._queue: List[ApprovalItem] = []
        self._next_id = 1

    def submit(
        self, tool_name: str, params: Dict[str, Any], preview: str, risk_tier: int = 1
    ) -> str:
        """Setur beiðni í biðröð. Skilar ID."""
        item_id = f"hitl-{self._next_id:04d}"
        self._next_id += 1

        item = ApprovalItem(
            item_id=item_id,
            tool_name=tool_name,
            params=params,
            preview=preview,
            risk_tier=risk_tier,
        )
        self._queue.append(item)
        print(f"[HITL] Beiðni {item_id} sett í biðröð: {tool_name} — {preview}")
        return item_id

    def approve(self, item_id: str) -> Optional[ApprovalItem]:
        """Samþykkir beiðni."""
        for item in self._queue:
            if item.item_id == item_id and item.status == "pending":
                item.status = "approved"
                item.decided_at = datetime.now(timezone.utc).isoformat()
                print(f"[HITL] ✅ Beiðni {item_id} samþykkt: {item.tool_name}")
                return item
        print(f"[HITL] ❌ Beiðni {item_id} fannst ekki eða þegar afgreidd")
        return None

    def reject(self, item_id: str) -> Optional[ApprovalItem]:
        """Hafnar beiðni."""
        for item in self._queue:
            if item.item_id == item_id and item.status == "pending":
                item.status = "rejected"
                item.decided_at = datetime.now(timezone.utc).isoformat()
                print(f"[HITL] ❌ Beiðni {item_id} hafnað: {item.tool_name}")
                return item
        print(f"[HITL] ❌ Beiðni {item_id} fannst ekki eða þegar afgreidd")
        return None

    def get_pending(self) -> List[ApprovalItem]:
        """Skilar öllum óafgreiddum beiðnum."""
        return [item for item in self._queue if item.status == "pending"]

    def get_all(self) -> List[ApprovalItem]:
        """Skilar öllum beiðnum."""
        return list(self._queue)


# ─── Keyrsla beint ───
if __name__ == "__main__":
    queue = ApprovalQueue()

    # Setja beiðni í biðröð
    id1 = queue.submit("send_email", {"to": "jon@internet.is", "subject": "Tilkynning"}, "Senda tölvupóst til jon@internet.is")
    id2 = queue.submit("send_email", {"to": "gudrun@internet.is", "subject": "Uppfærsla"}, "Senda tölvupóst til gudrun@internet.is")

    print(f"\n=== Óafgreiddar beiðnir ===")
    for item in queue.get_pending():
        print(f"  {item.item_id}: {item.tool_name} — {item.preview} [{item.status}]")

    # Samþykkja fyrstu
    queue.approve(id1)

    # Hafna seinni
    queue.reject(id2)

    print(f"\n=== Allar beiðnir eftir afgreiðslu ===")
    for item in queue.get_all():
        print(f"  {item.item_id}: {item.tool_name} — {item.status}")
