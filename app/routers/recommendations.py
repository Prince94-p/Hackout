from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.recommendation import Recommendation
from app.schemas.recommendations import RecommendationResponse
from app.auth import get_current_user, verify_factory_access
from app.services.recommendation_engine import generate_factory_recommendations

router = APIRouter(prefix="/api/factories/{id}/recommendations", tags=["Recommendations"])

@router.get("", response_model=List[RecommendationResponse])
def get_recommendations(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    recs = db.query(Recommendation).filter(Recommendation.factory_id == factory.id).all()

    if not recs or len(recs) == 0:
        recs = generate_factory_recommendations(factory, db)

    return [
        RecommendationResponse(
            id=r.id,
            code=r.code,
            title=r.title,
            description=r.description,
            category=r.category,
            target_process=r.target_process,
            root_cause=r.root_cause,
            carbon_saving_tco2e=r.carbon_saving_tco2e,
            reduction_pct=r.reduction_pct,
            estimated_cost_inr_lakhs=r.estimated_cost_inr_lakhs,
            payback_months=r.payback_months,
            effort_level=r.effort_level,
            confidence_pct=r.confidence_pct,
            disruption_level=r.disruption_level,
            assumption_reference=r.assumption_reference,
            derivation_type=r.derivation_type,
            justification=r.justification
        )
        for r in recs
    ]

@router.get("/{code_or_id}", response_model=RecommendationResponse)
def get_single_recommendation(
    id: int,
    code_or_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)

    r = None
    if code_or_id.isdigit():
        r = db.query(Recommendation).filter(
            Recommendation.factory_id == factory.id,
            Recommendation.id == int(code_or_id)
        ).first()

    if not r:
        r = db.query(Recommendation).filter(
            Recommendation.factory_id == factory.id,
            Recommendation.code == code_or_id
        ).first()

    if not r:
        recs = generate_factory_recommendations(factory, db)
        r = next((item for item in recs if item.code == code_or_id), None)
        if not r and len(recs) > 0:
            r = recs[0]

    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return RecommendationResponse(
        id=r.id,
        code=r.code,
        title=r.title,
        description=r.description,
        category=r.category,
        target_process=r.target_process,
        root_cause=r.root_cause,
        carbon_saving_tco2e=r.carbon_saving_tco2e,
        reduction_pct=r.reduction_pct,
        estimated_cost_inr_lakhs=r.estimated_cost_inr_lakhs,
        payback_months=r.payback_months,
        effort_level=r.effort_level,
        confidence_pct=r.confidence_pct,
        disruption_level=r.disruption_level,
        assumption_reference=r.assumption_reference,
        derivation_type=r.derivation_type,
        justification=r.justification
    )
