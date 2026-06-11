"""Pydantic API gagnastrúktúr fyrir HITL samskipti."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ToolAction(BaseModel):
    """Ein tól-aðgerð í áætlun."""
    tool: str = Field(..., description="Nafn tóls")
    params: Dict[str, Any] = Field(default_factory=dict, description="Færibreytur tóls")


class AgentPlan(BaseModel):
    """Áætlun frá Planner."""
    task_id: str
    steps: List[ToolAction] = Field(default_factory=list)
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0


class TaskStatus(BaseModel):
    """Staða verkefnis."""
    task_id: str
    description: str
    status: str = "pending"  # pending, in_progress, done, failed, frozen
    steps_completed: int = 0
    steps_total: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0


class HITLApprovalRequest(BaseModel):
    """Samþykkis-beiðni í biðröð."""
    item_id: str = Field(..., description="Einkvæmt ID")
    tool_name: str = Field(..., description="Nafn tóls sem krefst samþykkis")
    params: Dict[str, Any] = Field(default_factory=dict, description="Færibreytur tóls")
    preview: str = Field(..., description="Mannan-læsileg forskoðun")
    risk_tier: int = Field(1, ge=1, le=3, description="1=lágt, 2=miðlungs, 3=hátt (rautt)")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"


class HITLApprovalResponse(BaseModel):
    """Svar frá notanda við samþykkis-beiðni."""
    item_id: str
    decision: str  # "approved" eða "rejected"
    comment: Optional[str] = None


# ─── JSON sýnishorn ───
if __name__ == "__main__":
    import json

    req = HITLApprovalRequest(
        item_id="hitl-0001",
        tool_name="send_email",
        params={"to": "jon@internet.is", "subject": "Samninganalýsa", "body": "..."},
        preview="Senda tölvupóst til jon@internet.is með samninganalýsu",
        risk_tier=2,
    )

    print("=== HITLApprovalRequest (JSON sýnishorn) ===")
    print(json.dumps(req.model_dump(), indent=2, ensure_ascii=False))
