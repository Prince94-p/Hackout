from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hotspot import Hotspot
from app.schemas.hotspot import RootCauseResponse
from app.auth import get_current_user, verify_factory_access
from app.services.hotspot_engine import evaluate_and_generate_hotspots
from app.services.root_cause_engine import diagnose_root_cause

router = APIRouter(prefix="/api/factories/{id}/root-cause", tags=["Root Cause"])

@router.get("", response_model=RootCauseResponse)
def get_root_cause(
    id: int,
    hotspot_code: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)

    # Get hotspot
    query = db.query(Hotspot).filter(Hotspot.factory_id == factory.id)
    if hotspot_code:
        h = query.filter(Hotspot.code == hotspot_code).first()
    else:
        h = query.order_by(Hotspot.rank.asc()).first()

    if not h:
        all_h = evaluate_and_generate_hotspots(factory, db)
        h = all_h[0] if all_h else None

    if not h:
        raise HTTPException(status_code=404, detail="No active hotspot found for root cause diagnosis")

    diagnosis = diagnose_root_cause(factory, h)
    return RootCauseResponse(**diagnosis)
