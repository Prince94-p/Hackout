import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.factory import Factory
from app.models.emissions import EmissionRecord
from app.models.activity import Process
from app.schemas.emissions import EmissionCalculateResponse, EmissionSummaryResponse
from app.auth import get_current_user, verify_factory_access
from app.services.carbon_engine import calculate_factory_emissions

router = APIRouter(prefix="/api/factories/{id}", tags=["Emissions"])

@router.post("/calculate", response_model=EmissionCalculateResponse)
def calculate_emissions(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    record = calculate_factory_emissions(factory, db)

    breakdown = json.loads(record.confidence_breakdown) if record.confidence_breakdown else {}
    traceability = json.loads(record.factor_traceability) if record.factor_traceability else []

    return EmissionCalculateResponse(
        total_tco2e=record.total_tco2e,
        energy_tco2e=record.energy_tco2e,
        material_tco2e=record.material_tco2e,
        waste_tco2e=record.waste_tco2e,
        energy_pct=record.energy_pct,
        material_pct=record.material_pct,
        waste_pct=record.waste_pct,
        largest_source=record.largest_source,
        confidence=record.confidence_score,
        confidence_breakdown=breakdown,
        factor_traceability=traceability,
        calculation_date=record.calculation_date
    )

@router.get("/emissions/summary", response_model=EmissionSummaryResponse)
def get_emissions_summary(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)

    record = db.query(EmissionRecord).filter(
        EmissionRecord.factory_id == factory.id
    ).order_by(EmissionRecord.calculation_date.desc()).first()

    if not record or record.total_tco2e <= 0:
        return EmissionSummaryResponse(
            has_calculation=False,
            factory_name=factory.name,
            baseline=0.0,
            energy_tco2e=0.0,
            material_tco2e=0.0,
            waste_tco2e=0.0,
            energy_pct=0.0,
            material_pct=0.0,
            waste_pct=0.0,
            largest_source="None",
            top_share_pct=0.0,
            confidence=0.0,
            source_distribution=[],
            investigation_queue=[]
        )

    breakdown = json.loads(record.confidence_breakdown) if record.confidence_breakdown else None

    # Top category share
    top_share = max(record.energy_pct, record.material_pct, record.waste_pct)

    # Detect priority leak from processes
    grid_factor = factory.energy_sources[0].emission_factor if factory.energy_sources else 0.48
    processes = factory.processes

    # Sort processes by potential carbon or leakage
    priority_leak = "Compressed Air"
    priority_leak_pct = "28%"
    wasted_kwh = 0.0
    priority_footprint = 0.0
    operating_pressure = "7.5 bar"

    # Dynamic investigation queue
    queue = []
    rank = 1

    # Check for compressed air
    air_proc = next((p for p in processes if "air" in p.name.lower() or "compress" in p.name.lower()), None)
    if air_proc:
        p_kwh = air_proc.annual_energy_kwh or 0.0
        p_leak = air_proc.estimated_leakage_percent or 0.0
        p_bar = air_proc.operating_pressure_bar or 0.0
        p_carbon = (p_kwh * grid_factor) / 1000.0
        p_wasted = (p_kwh * (p_leak / 100.0)) if p_leak > 0 else 0.0

        priority_leak = air_proc.name
        priority_leak_pct = f"{int(p_leak)}% leakage" if p_leak > 0 else "Optimized"
        wasted_kwh = round(p_wasted, 0)
        priority_footprint = round(p_carbon, 1)
        operating_pressure = f"{p_bar} bar" if p_bar > 0 else "Nominal"

        queue.append({
            "rank": f"{rank:02d}",
            "code": "compressed-air",
            "name": air_proc.name,
            "path": "Energy → Utilities",
            "footprint": f"{round(p_carbon, 0)} tCO₂e",
            "signal": f"{int(p_leak)}%",
            "signal_label": "leakage signal"
        })
        rank += 1

    # Check for CNC or production machinery
    cnc_proc = next((p for p in processes if "cnc" in p.name.lower() or "machin" in p.name.lower()), None)
    if cnc_proc:
        p_kwh = cnc_proc.annual_energy_kwh or 0.0
        p_carbon = (p_kwh * grid_factor) / 1000.0
        queue.append({
            "rank": f"{rank:02d}",
            "code": "cnc",
            "name": cnc_proc.name,
            "path": "Energy → Production",
            "footprint": f"{round(p_carbon, 0)} tCO₂e",
            "signal": "High",
            "signal_label": "idle energy load"
        })
        rank += 1

    # Material input hotspot
    if factory.material_inputs:
        mat = factory.material_inputs[0]
        mat_carbon = (mat.annual_quantity * mat.emission_factor) / 1000.0
        queue.append({
            "rank": f"{rank:02d}",
            "code": "aluminium",
            "name": mat.material_type,
            "path": "Materials → Input",
            "footprint": f"{round(mat_carbon, 0)} tCO₂e",
            "signal": f"{int(mat.recycled_content_percent)}%",
            "signal_label": "recycled content"
        })
        rank += 1

    # If queue is empty (e.g. no custom processes entered yet), add defaults from active streams
    if not queue:
        if record.energy_tco2e > 0:
            queue.append({
                "rank": "01",
                "code": "energy",
                "name": "Energy & Utilities",
                "path": "Scope 2 → Grid Power",
                "footprint": f"{round(record.energy_tco2e, 0)} tCO₂e",
                "signal": f"{record.energy_pct}%",
                "signal_label": "energy share"
            })
        if record.material_tco2e > 0:
            queue.append({
                "rank": "02",
                "code": "materials",
                "name": "Raw Material Inputs",
                "path": "Scope 3 → Upstream Materials",
                "footprint": f"{round(record.material_tco2e, 0)} tCO₂e",
                "signal": f"{record.material_pct}%",
                "signal_label": "material share"
            })
        if record.waste_tco2e > 0:
            queue.append({
                "rank": "03",
                "code": "waste",
                "name": "Process Waste Streams",
                "path": "Scope 3 → End of Life",
                "footprint": f"{round(record.waste_tco2e, 0)} tCO₂e",
                "signal": f"{record.waste_pct}%",
                "signal_label": "waste share"
            })

    source_distribution = [
        {"category": "Energy", "tco2e": record.energy_tco2e, "pct": record.energy_pct, "color": "#ff7b45"},
        {"category": "Materials", "tco2e": record.material_tco2e, "pct": record.material_pct, "color": "#238761"},
        {"category": "Waste", "tco2e": record.waste_tco2e, "pct": record.waste_pct, "color": "#2b6de8"}
    ]

    return EmissionSummaryResponse(
        has_calculation=True,
        factory_name=factory.name,
        baseline=record.total_tco2e,
        energy_tco2e=record.energy_tco2e,
        material_tco2e=record.material_tco2e,
        waste_tco2e=record.waste_tco2e,
        energy_pct=record.energy_pct,
        material_pct=record.material_pct,
        waste_pct=record.waste_pct,
        largest_source=record.largest_source,
        top_share_pct=top_share,
        priority_leak=priority_leak,
        priority_leak_pct=priority_leak_pct,
        wasted_kwh=wasted_kwh,
        priority_footprint=priority_footprint,
        operating_pressure=operating_pressure,
        confidence=record.confidence_score,
        confidence_breakdown=breakdown,
        source_distribution=source_distribution,
        investigation_queue=queue[:3]
    )
