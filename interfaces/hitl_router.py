"""HITL API Router — endapunktar fyrir samþykkis-biðröð."""

from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from typing import List
import json, os
from datetime import datetime, timezone
from core.agent.hitl_db import HITLDatabase
from core.audit_writer import log_hitl

router = APIRouter(prefix="/api/hitl", tags=["HITL"])
db = HITLDatabase()

def _write_hitl_audit(item_id, decision, approver_sub):
    log_hitl(item_id, decision, approver_sub)

@router.get("/count")
async def get_pending_count() -> dict:
    """Skilar fjölda beiðna í biðröð — opinn endapunktur."""
    items = db.get_pending()
    return {"count": len(items)}

@router.get("/queue")
async def get_pending() -> List[dict]:
    items = db.get_pending()
    for item in items:
        if isinstance(item.get("params"), str):
            item["params"] = json.loads(item["params"])
    return items

@router.post("/approve/{item_id}")
async def approve_item(item_id: str, request: Request) -> dict:
    approver_sub = getattr(request.state, "user_claims", {}).get("sub", "")
    success = db.update_status(item_id, "approved", caller="hitl_router", approver_sub=approver_sub)
    if not success:
        raise HTTPException(status_code=404, detail="Beidni fannst ekki eda thegar afgreidd")
    _write_hitl_audit(item_id, "approved", approver_sub)
    return {"item_id": item_id, "status": "approved", "approver_sub": approver_sub}

@router.post("/reject/{item_id}")
async def reject_item(item_id: str, request: Request) -> dict:
    approver_sub = getattr(request.state, "user_claims", {}).get("sub", "")
    success = db.update_status(item_id, "rejected", approver_sub=approver_sub)
    if not success:
        raise HTTPException(status_code=404, detail="Beidni fannst ekki eda thegar afgreidd")
    _write_hitl_audit(item_id, "rejected", approver_sub)
    return {"item_id": item_id, "status": "rejected", "approver_sub": approver_sub}
