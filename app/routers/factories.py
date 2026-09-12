import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.factory import Factory
from app.models.activity import EnergySource, MaterialInput, Process, WasteStream
from app.schemas.factory import FactoryCreate, FactoryResponse
from app.auth import get_current_user, verify_factory_access

router = APIRouter(prefix="/api/factories", tags=["Factories"])

@router.post("", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
def create_factory(
    payload: FactoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    selected_proc_str = json.dumps(payload.selected_processes) if payload.selected_processes else "[]"
    factory = Factory(
        user_id=current_user.id,
        name=payload.name.strip(),
        industry=payload.industry.strip(),
        location=payload.location.strip(),
        reporting_period=payload.reporting_period.strip(),
        annual_production=payload.annual_production,
        production_unit=payload.production_unit.strip(),
        selected_processes=selected_proc_str,
        is_demo=False
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory

@router.get("", response_model=List[FactoryResponse])
def list_factories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Factory).filter(Factory.user_id == current_user.id).order_by(Factory.created_at.desc()).all()

@router.get("/{id}", response_model=FactoryResponse)
def get_factory(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    return factory

@router.post("/demo", response_model=FactoryResponse)
def get_or_create_demo_factory(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if this user already has a demo factory
    demo = db.query(Factory).filter(
        Factory.user_id == current_user.id,
        Factory.is_demo == True
    ).first()

    if demo:
        return demo

    # Create the demo factory
    processes = [
        "CNC Machining & Turning",
        "Compressed Air System",
        "Heat Treatment",
        "Quality Inspection"
    ]

    demo = Factory(
        user_id=current_user.id,
        name="Apex Components Pvt. Ltd.",
        industry="Automotive Components",
        location="Gujarat, India",
        reporting_period="FY 2024-2025",
        annual_production=120000.0,
        production_unit="parts/year",
        selected_processes=json.dumps(processes),
        is_demo=True
    )
    db.add(demo)
    db.commit()
    db.refresh(demo)

    # Seed verified demo activity streams
    energy = EnergySource(
        factory_id=demo.id,
        source_type="Grid Electricity",
        annual_consumption=1250000.0,
        unit="kWh/year",
        emission_factor=0.48,
        factor_source="Configured Grid Factor (CEA 2024)"
    )
    db.add(energy)

    material = MaterialInput(
        factory_id=demo.id,
        material_type="Virgin Aluminium",
        annual_quantity=50000.0,
        unit="kg/year",
        recycled_content_percent=20.0,
        emission_factor=8.0
    )
    db.add(material)

    p_cnc = Process(
        factory_id=demo.id,
        name="CNC Machining & Turning",
        equipment="8 × VMC 5-Axis Spindles",
        operating_hours=6200.0,
        primary_energy_source="Grid Electricity",
        operating_pressure_bar=0.0,
        estimated_leakage_percent=0.0,
        annual_energy_kwh=475000.0,
        notes="High spindle idle runtime observed during tool changes and batch transition."
    )
    db.add(p_cnc)

    p_air = Process(
        factory_id=demo.id,
        name="Compressed Air System",
        equipment="2 × 75 kW Screw Compressors",
        operating_hours=7200.0,
        primary_energy_source="Grid Electricity",
        operating_pressure_bar=7.5,
        estimated_leakage_percent=28.0,
        annual_energy_kwh=337500.0,
        notes="Distribution piping network shows audible leakage; line pressure maintained at 7.5 bar."
    )
    db.add(p_air)

    waste = WasteStream(
        factory_id=demo.id,
        waste_type="Aluminium Machining Swarf",
        annual_quantity=75000.0,
        unit="kg/year",
        treatment_method="Landfill / Disposal",
        emission_factor=2.0
    )
    db.add(waste)

    db.commit()
    return demo
