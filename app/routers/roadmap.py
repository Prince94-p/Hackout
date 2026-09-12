from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.roadmap import Roadmap, RoadmapAction
from app.schemas.roadmap import RoadmapResponse
from app.auth import get_current_user, verify_factory_access
from app.services.roadmap_engine import generate_factory_roadmap

router = APIRouter(prefix="/api/factories/{id}/roadmap", tags=["Roadmap"])

class RoadmapGenerateRequest(BaseModel):
    preferred_scenario_id: Optional[int] = None

@router.get("", response_model=RoadmapResponse)
def get_roadmap(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)

    roadmap = db.query(Roadmap).filter(Roadmap.factory_id == factory.id).first()
    if not roadmap:
        result = generate_factory_roadmap(factory, db)
        return result

    # Format response from saved DB records
    actions = db.query(RoadmapAction).filter(
        RoadmapAction.roadmap_id == roadmap.id
    ).order_by(RoadmapAction.order_index.asc()).all()

    # Build timeline trajectory from saved actions
    timeline = [{"month": "Month 0", "label": "Baseline", "footprint_tco2e": roadmap.baseline_tco2e}]
    months_map = ["Month 3", "Month 6", "Month 12", "Month 24"]
    current_fp = roadmap.baseline_tco2e
    for i, a in enumerate(actions):
        current_fp = max(roadmap.target_footprint_tco2e, round(current_fp - a.carbon_saving_tco2e, 1))
        m_label = months_map[min(i, len(months_map) - 1)]
        timeline.append({
            "month": m_label,
            "label": f"Post {a.action_title[:20]}...",
            "footprint_tco2e": current_fp
        })

    if len(timeline) == 1:
        timeline.append({"month": "Month 24", "label": "Target", "footprint_tco2e": roadmap.target_footprint_tco2e})

    return RoadmapResponse(
        id=roadmap.id,
        factory_id=factory.id,
        baseline_tco2e=roadmap.baseline_tco2e,
        planned_saving_tco2e=roadmap.planned_saving_tco2e,
        target_footprint_tco2e=roadmap.target_footprint_tco2e,
        reduction_percent=roadmap.reduction_percent,
        total_cost_inr_lakhs=roadmap.total_cost_inr_lakhs,
        timeline_steps=timeline,
        actions=[
            {
                "id": a.id,
                "order_index": a.order_index,
                "action_title": a.action_title,
                "phase_label": a.phase_label,
                "carbon_saving_tco2e": a.carbon_saving_tco2e,
                "cost_inr_lakhs": a.cost_inr_lakhs,
                "effort_level": a.effort_level,
                "confidence_pct": a.confidence_pct,
                "status": a.status
            }
            for a in actions
        ]
    )

@router.post("", response_model=RoadmapResponse)
def create_or_regenerate_roadmap(
    id: int,
    payload: Optional[RoadmapGenerateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    pref_id = payload.preferred_scenario_id if payload else None
    result = generate_factory_roadmap(factory, db, preferred_scenario_id=pref_id)
    return result
