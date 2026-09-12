import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hotspot import Hotspot
from app.schemas.hotspot import HotspotResponse
from app.auth import get_current_user, verify_factory_access
from app.services.hotspot_engine import evaluate_and_generate_hotspots

router = APIRouter(prefix="/api/factories/{id}/hotspots", tags=["Hotspots"])

@router.get("", response_model=List[HotspotResponse])
def get_hotspots(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    hotspots = db.query(Hotspot).filter(Hotspot.factory_id == factory.id).order_by(Hotspot.rank.asc()).all()

    if not hotspots or len(hotspots) == 0:
        hotspots = evaluate_and_generate_hotspots(factory, db)

    results = []
    for h in hotspots:
        details = json.loads(h.details_json) if h.details_json else {}
        results.append(HotspotResponse(
            id=h.id,
            rank=h.rank,
            code=h.code,
            title=h.title,
            category=h.category,
            branch_path=h.branch_path,
            carbon_tco2e=h.carbon_tco2e,
            share_pct=h.share_pct,
            signal_type=h.signal_type,
            signal_value=h.signal_value,
            operating_condition=h.operating_condition,
            confidence_pct=h.confidence_pct,
            details=details
        ))
    return results

@router.get("/{code}", response_model=HotspotResponse)
def get_hotspot_by_code(
    id: int,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    h = db.query(Hotspot).filter(
        Hotspot.factory_id == factory.id,
        Hotspot.code == code
    ).first()

    if not h:
        # Evaluate if needed
        all_h = evaluate_and_generate_hotspots(factory, db)
        h = next((item for item in all_h if item.code == code), None)
        if not h and len(all_h) > 0:
            h = all_h[0]

    if not h:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    details = json.loads(h.details_json) if h.details_json else {}
    return HotspotResponse(
        id=h.id,
        rank=h.rank,
        code=h.code,
        title=h.title,
        category=h.category,
        branch_path=h.branch_path,
        carbon_tco2e=h.carbon_tco2e,
        share_pct=h.share_pct,
        signal_type=h.signal_type,
        signal_value=h.signal_value,
        operating_condition=h.operating_condition,
        confidence_pct=h.confidence_pct,
        details=details
    )
