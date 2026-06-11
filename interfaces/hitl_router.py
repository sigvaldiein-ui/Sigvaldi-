"""HITL API Router — endapunktar fyrir samþykkis-biðröð."""

from fastapi import APIRouter, HTTPException
from typing import List
import json
from core.agent.hitl_db import HITLDatabase

router = APIRouter(prefix="/api/hitl", tags=["HITL"])
db = HITLDatabase()

@router.get("/queue")
async def get_pending() -> List[dict]:
    items = db.get_pending()
    for item in items:
        if isinstance(item.get("params"), str):
            item["params"] = json.loads(item["params"])
    return items

@router.post("/approve/{item_id}")
async def approve_item(item_id: str) -> dict:
    success = db.update_status(item_id, "approved")
    if not success:
        raise HTTPException(status_code=404, detail="Beiðni fannst ekki")
    return {"item_id": item_id, "status": "approved"}

@router.post("/reject/{item_id}")
async def reject_item(item_id: str) -> dict:
    success = db.update_status(item_id, "rejected")
    if not success:
        raise HTTPException(status_code=404, detail="Beiðni fannst ekki")
    return {"item_id": item_id, "status": "rejected"}
