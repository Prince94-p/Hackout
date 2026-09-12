from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.factory import Factory
from app.models.emissions import EmissionRecord
from app.models.recommendation import Recommendation
from app.models.scenario import Scenario
from app.models.roadmap import Roadmap, RoadmapAction
from app.services.recommendation_engine import generate_factory_recommendations

def generate_factory_roadmap(
    factory: Factory,
    db: Session,
    preferred_scenario_id: Optional[int] = None
) -> Dict[str, Any]:
    # 1. Authoritative Baseline
    rec = db.query(EmissionRecord).filter(
        EmissionRecord.factory_id == factory.id
    ).order_by(EmissionRecord.calculation_date.desc()).first()

    baseline = rec.total_tco2e if rec else (1150.0 if factory.is_demo else 0.0)

    # 2. Existing Recommendations
    recs = db.query(Recommendation).filter(Recommendation.factory_id == factory.id).all()
    if not recs:
        recs = generate_factory_recommendations(factory, db)

    # 3. Check for preferred or latest scenario
    scenario = None
    if preferred_scenario_id:
        scenario = db.query(Scenario).filter(
            Scenario.factory_id == factory.id,
            Scenario.id == preferred_scenario_id
        ).first()
    if not scenario:
        scenario = db.query(Scenario).filter(
            Scenario.factory_id == factory.id
        ).order_by(Scenario.created_at.desc()).first()

    # Clear prior saved roadmap for clean regeneration
    db.query(Roadmap).filter(Roadmap.factory_id == factory.id).delete()
    db.commit()

    # If demo factory without custom scenario, yield verified demo target roadmap
    if factory.is_demo and not scenario:
        demo_actions_spec = [
            {
                "order_index": 1,
                "action_title": "Compressor Optimization & Leak Remediation",
                "phase_label": "Phase 1: 0–3 Months (Quick Wins)",
                "carbon_saving_tco2e": 74.0,
                "cost_inr_lakhs": 1.6,
                "effort_level": "Low",
                "confidence_pct": 88.0,
                "status": "Ready to Deploy"
            },
            {
                "order_index": 2,
                "action_title": "Increase Recycled Aluminium Share",
                "phase_label": "Phase 2: 3–6 Months (Material Circularity)",
                "carbon_saving_tco2e": 105.0,
                "cost_inr_lakhs": 3.8,
                "effort_level": "Medium",
                "confidence_pct": 82.0,
                "status": "Supplier Qualification"
            },
            {
                "order_index": 3,
                "action_title": "Waste Heat Recovery (Flue Gas Recuperation)",
                "phase_label": "Phase 3: 6–12 Months (Thermal Recovery)",
                "carbon_saving_tco2e": 62.0,
                "cost_inr_lakhs": 5.2,
                "effort_level": "High",
                "confidence_pct": 76.0,
                "status": "Engineering Review"
            }
        ]

        total_saving = 241.0  # 74 + 105 + 62
        target_footprint = round(baseline - total_saving, 1)
        red_pct = round((total_saving / baseline) * 100.0, 1)
        total_cost = 10.6

        roadmap = Roadmap(
            factory_id=factory.id,
            baseline_tco2e=baseline,
            planned_saving_tco2e=total_saving,
            target_footprint_tco2e=target_footprint,
            reduction_percent=red_pct,
            total_cost_inr_lakhs=total_cost,
            created_at=datetime.now(timezone.utc)
        )
        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)

        actions_out = []
        for a in demo_actions_spec:
            action = RoadmapAction(
                roadmap_id=roadmap.id,
                order_index=a["order_index"],
                action_title=a["action_title"],
                phase_label=a["phase_label"],
                carbon_saving_tco2e=a["carbon_saving_tco2e"],
                cost_inr_lakhs=a["cost_inr_lakhs"],
                effort_level=a["effort_level"],
                confidence_pct=a["confidence_pct"],
                status=a["status"]
            )
            db.add(action)
            actions_out.append(action)
        db.commit()

        timeline = [
            {"month": "Month 0", "label": "Baseline", "footprint_tco2e": 1150.0},
            {"month": "Month 3", "label": "Post Phase 1", "footprint_tco2e": 1076.0},
            {"month": "Month 6", "label": "Post Phase 2", "footprint_tco2e": 971.0},
            {"month": "Month 12", "label": "Post Phase 3", "footprint_tco2e": 909.0},
            {"month": "Month 24", "label": "Target Footprint", "footprint_tco2e": 909.0}
        ]

        return {
            "id": roadmap.id,
            "factory_id": factory.id,
            "baseline_tco2e": baseline,
            "planned_saving_tco2e": total_saving,
            "target_footprint_tco2e": target_footprint,
            "reduction_percent": red_pct,
            "total_cost_inr_lakhs": total_cost,
            "timeline_steps": timeline,
            "actions": [
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
                for a in actions_out
            ]
        }

    # Custom factory: deterministic prioritization
    if baseline <= 0 or not recs:
        # Empty roadmap response
        return {
            "id": None,
            "factory_id": factory.id,
            "baseline_tco2e": 0.0,
            "planned_saving_tco2e": 0.0,
            "target_footprint_tco2e": 0.0,
            "reduction_percent": 0.0,
            "total_cost_inr_lakhs": 0.0,
            "timeline_steps": [],
            "actions": []
        }

    # Sort recommendations by effort/payback/saving score
    sorted_recs = sorted(
        recs,
        key=lambda r: (
            0 if r.effort_level.lower() == "low" else (1 if r.effort_level.lower() == "medium" else 2),
            r.payback_months or 12.0,
            -r.carbon_saving_tco2e
        )
    )

    # If scenario exists, prioritize its recommendation
    selected_actions = []
    seen_codes = set()

    if scenario:
        target_rec = next((r for r in recs if r.id == scenario.recommendation_id), None) or scenario.recommendation
        title = scenario.title or (target_rec.title if target_rec else "Simulated Decarbonization Action")
        conf = target_rec.confidence_pct if target_rec else (scenario.recommendation.confidence_pct if scenario.recommendation else 85.0)
        act_code = target_rec.code if target_rec else "scenario"
        selected_actions.append({
            "action_title": title,
            "phase_label": "Phase 1: 0–3 Months (Simulated Priority)",
            "carbon_saving_tco2e": scenario.effective_saving_tco2e,
            "cost_inr_lakhs": scenario.estimated_cost_inr_lakhs,
            "effort_level": target_rec.effort_level if target_rec else "Low",
            "confidence_pct": conf,
            "status": "Ready to Deploy",
            "code": act_code
        })
        if act_code:
            seen_codes.add(act_code)

    phase_labels = [
        "Phase 1: 0–3 Months (Quick Wins)",
        "Phase 2: 3–6 Months (Process Optimization)",
        "Phase 3: 6–12 Months (Equipment Retrofits)",
        "Phase 4: 12–24 Months (Clean Energy Transition)"
    ]

    phase_idx = 1 if scenario else 0
    for r in sorted_recs:
        if r.code in seen_codes or r.carbon_saving_tco2e <= 0:
            continue
        seen_codes.add(r.code)
        label = phase_labels[min(phase_idx, len(phase_labels) - 1)]
        selected_actions.append({
            "action_title": r.title,
            "phase_label": label,
            "carbon_saving_tco2e": r.carbon_saving_tco2e,
            "cost_inr_lakhs": r.estimated_cost_inr_lakhs,
            "effort_level": r.effort_level,
            "confidence_pct": r.confidence_pct,
            "status": "Planned",
            "code": r.code
        })
        phase_idx += 1
        if len(selected_actions) >= 4:
            break

    # Sum savings & costs
    total_saving = round(sum(a["carbon_saving_tco2e"] for a in selected_actions), 1)
    total_saving = min(total_saving, round(baseline * 0.85, 1))  # Cap realistic max saving
    target_footprint = max(0.0, round(baseline - total_saving, 1))
    red_pct = round((total_saving / baseline) * 100.0, 1) if baseline > 0 else 0.0
    total_cost = round(sum(a["cost_inr_lakhs"] for a in selected_actions), 2)

    # Persist in DB
    roadmap = Roadmap(
        factory_id=factory.id,
        baseline_tco2e=baseline,
        planned_saving_tco2e=total_saving,
        target_footprint_tco2e=target_footprint,
        reduction_percent=red_pct,
        total_cost_inr_lakhs=total_cost,
        created_at=datetime.now(timezone.utc)
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)

    db_actions = []
    for i, a in enumerate(selected_actions, 1):
        action = RoadmapAction(
            roadmap_id=roadmap.id,
            order_index=i,
            action_title=a["action_title"],
            phase_label=a["phase_label"],
            carbon_saving_tco2e=a["carbon_saving_tco2e"],
            cost_inr_lakhs=a["cost_inr_lakhs"],
            effort_level=a["effort_level"],
            confidence_pct=a["confidence_pct"],
            status=a["status"]
        )
        db.add(action)
        db_actions.append(action)
    db.commit()

    # Calculate step-by-step trajectory
    current_fp = baseline
    timeline = [{"month": "Month 0", "label": "Baseline", "footprint_tco2e": round(baseline, 1)}]

    months_map = ["Month 3", "Month 6", "Month 12", "Month 24"]
    for i, a in enumerate(selected_actions):
        current_fp = max(target_footprint, round(current_fp - a["carbon_saving_tco2e"], 1))
        m_label = months_map[min(i, len(months_map) - 1)]
        timeline.append({
            "month": m_label,
            "label": f"Post {a['action_title'][:20]}...",
            "footprint_tco2e": current_fp
        })

    if len(timeline) == 1:
        timeline.append({"month": "Month 24", "label": "Target", "footprint_tco2e": target_footprint})

    return {
        "id": roadmap.id,
        "factory_id": factory.id,
        "baseline_tco2e": round(baseline, 1),
        "planned_saving_tco2e": total_saving,
        "target_footprint_tco2e": target_footprint,
        "reduction_percent": red_pct,
        "total_cost_inr_lakhs": total_cost,
        "timeline_steps": timeline,
        "actions": [
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
            for a in db_actions
        ]
    }
