from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.recommendation import Recommendation
from app.models.emissions import EmissionRecord
from app.models.scenario import Scenario
from app.schemas.scenarios import (
    ScenarioPreviewRequest,
    ScenarioPreviewResponse,
    ScenarioSaveRequest,
    ScenarioResponse
)
from app.auth import get_current_user, verify_factory_access
from app.services.recommendation_engine import generate_factory_recommendations

router = APIRouter(prefix="/api/factories/{id}/scenarios", tags=["Simulator"])

def _get_recommendation_and_baseline(
    factory,
    req: ScenarioPreviewRequest,
    db: Session
):
    rec = None
    if req.recommendation_id:
        rec = db.query(Recommendation).filter(
            Recommendation.factory_id == factory.id,
            Recommendation.id == req.recommendation_id
        ).first()

    if not rec and req.recommendation_code:
        rec = db.query(Recommendation).filter(
            Recommendation.factory_id == factory.id,
            Recommendation.code == req.recommendation_code
        ).first()

    if not rec:
        recs = db.query(Recommendation).filter(Recommendation.factory_id == factory.id).all()
        if not recs:
            recs = generate_factory_recommendations(factory, db)
        if recs:
            rec = recs[0]

    if not rec:
        raise HTTPException(
            status_code=400,
            detail="No recommendation found to simulate. Please calculate baseline first."
        )

    # Get baseline footprint from latest calculation
    record = db.query(EmissionRecord).filter(
        EmissionRecord.factory_id == factory.id
    ).order_by(EmissionRecord.calculation_date.desc()).first()
    baseline = record.total_tco2e if record else (1150.0 if factory.is_demo else max(100.0, rec.carbon_saving_tco2e * 5))
    if baseline <= 0:
        baseline = 1150.0 if factory.is_demo else max(100.0, rec.carbon_saving_tco2e * 5)

    return rec, baseline

@router.post("/preview", response_model=ScenarioPreviewResponse)
def preview_scenario(
    id: int,
    payload: ScenarioPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    rec, baseline = _get_recommendation_and_baseline(factory, payload, db)

    # Deterministic simulation calculation
    saving_multiplier = (payload.implementation_percent / 100.0) * (payload.performance_percent / 100.0)
    effective_saving = round(rec.carbon_saving_tco2e * saving_multiplier, 1)
    future_footprint = max(0.0, round(baseline - effective_saving, 1))
    reduction_pct = round((effective_saving / max(baseline, 0.001)) * 100.0, 1)
    
    cost_multiplier = (payload.implementation_percent / 100.0) * (1.0 + (payload.cost_variation_percent / 100.0))
    cost = round(rec.estimated_cost_inr_lakhs * cost_multiplier, 2)

    return ScenarioPreviewResponse(
        baseline_tco2e=round(baseline, 1),
        recommendation_title=rec.title,
        implementation_percent=payload.implementation_percent,
        performance_percent=payload.performance_percent,
        cost_variation_percent=payload.cost_variation_percent,
        effective_saving_tco2e=effective_saving,
        future_footprint_tco2e=future_footprint,
        reduction_percent=reduction_pct,
        estimated_cost_inr_lakhs=cost,
        confidence_pct=rec.confidence_pct
    )

@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def save_scenario(
    id: int,
    payload: ScenarioSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    rec, baseline = _get_recommendation_and_baseline(factory, payload, db)

    # Calculate
    saving_multiplier = (payload.implementation_percent / 100.0) * (payload.performance_percent / 100.0)
    effective_saving = round(rec.carbon_saving_tco2e * saving_multiplier, 1)
    future_footprint = max(0.0, round(baseline - effective_saving, 1))
    reduction_pct = round((effective_saving / max(baseline, 0.001)) * 100.0, 1)
    cost_multiplier = (payload.implementation_percent / 100.0) * (1.0 + (payload.cost_variation_percent / 100.0))
    cost = round(rec.estimated_cost_inr_lakhs * cost_multiplier, 2)

    title = payload.title or f"{rec.title} ({int(payload.implementation_percent)}% Impl)"

    scenario = Scenario(
        factory_id=factory.id,
        recommendation_id=rec.id,
        title=title,
        implementation_percent=payload.implementation_percent,
        performance_percent=payload.performance_percent,
        cost_variation_percent=payload.cost_variation_percent,
        effective_saving_tco2e=effective_saving,
        future_footprint_tco2e=future_footprint,
        reduction_percent=reduction_pct,
        estimated_cost_inr_lakhs=cost
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return ScenarioResponse(
        id=scenario.id,
        factory_id=scenario.factory_id,
        baseline_tco2e=round(baseline, 1),
        recommendation_title=rec.title,
        implementation_percent=scenario.implementation_percent,
        performance_percent=scenario.performance_percent,
        cost_variation_percent=scenario.cost_variation_percent,
        effective_saving_tco2e=scenario.effective_saving_tco2e,
        future_footprint_tco2e=scenario.future_footprint_tco2e,
        reduction_percent=scenario.reduction_percent,
        estimated_cost_inr_lakhs=scenario.estimated_cost_inr_lakhs,
        confidence_pct=rec.confidence_pct,
        title=scenario.title,
        created_at=scenario.created_at
    )

@router.get("", response_model=List[ScenarioResponse])
def list_scenarios(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    scenarios = db.query(Scenario).filter(Scenario.factory_id == factory.id).order_by(Scenario.created_at.desc()).all()

    # Get baseline from latest calculation
    record = db.query(EmissionRecord).filter(
        EmissionRecord.factory_id == factory.id
    ).order_by(EmissionRecord.calculation_date.desc()).first()
    baseline = record.total_tco2e if record else (1150.0 if factory.is_demo else 1000.0)
    if baseline <= 0:
        baseline = 1150.0 if factory.is_demo else 1000.0

    return [
        ScenarioResponse(
            id=s.id,
            factory_id=s.factory_id,
            baseline_tco2e=round(baseline, 1),
            recommendation_title=s.recommendation.title if s.recommendation else s.title,
            title=s.title,
            implementation_percent=s.implementation_percent,
            performance_percent=s.performance_percent,
            cost_variation_percent=s.cost_variation_percent,
            effective_saving_tco2e=s.effective_saving_tco2e,
            future_footprint_tco2e=s.future_footprint_tco2e,
            reduction_percent=s.reduction_percent,
            estimated_cost_inr_lakhs=s.estimated_cost_inr_lakhs,
            confidence_pct=s.recommendation.confidence_pct if s.recommendation else 80.0,
            created_at=s.created_at
        )
        for s in scenarios
    ]
