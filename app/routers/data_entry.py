from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.activity import EnergySource, MaterialInput, Process, WasteStream
from app.schemas.activity import ActivityDataPayload, ActivityDataResponse
from app.auth import get_current_user, verify_factory_access

router = APIRouter(prefix="/api/factories/{id}", tags=["Activity Data"])

@router.get("/data", response_model=ActivityDataResponse)
def get_factory_data(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)
    return ActivityDataResponse(
        energy_sources=[
            {
                "id": es.id,
                "source_type": es.source_type,
                "annual_consumption": es.annual_consumption,
                "unit": es.unit,
                "emission_factor": es.emission_factor,
                "factor_source": es.factor_source
            }
            for es in factory.energy_sources
        ],
        material_inputs=[
            {
                "id": mi.id,
                "material_type": mi.material_type,
                "annual_quantity": mi.annual_quantity,
                "unit": mi.unit,
                "recycled_content_percent": mi.recycled_content_percent,
                "emission_factor": mi.emission_factor
            }
            for mi in factory.material_inputs
        ],
        processes=[
            {
                "id": p.id,
                "name": p.name,
                "equipment": p.equipment,
                "operating_hours": p.operating_hours,
                "primary_energy_source": p.primary_energy_source,
                "operating_pressure_bar": p.operating_pressure_bar,
                "estimated_leakage_percent": p.estimated_leakage_percent,
                "annual_energy_kwh": p.annual_energy_kwh,
                "notes": p.notes
            }
            for p in factory.processes
        ],
        waste_streams=[
            {
                "id": ws.id,
                "waste_type": ws.waste_type,
                "annual_quantity": ws.annual_quantity,
                "unit": ws.unit,
                "treatment_method": ws.treatment_method,
                "emission_factor": ws.emission_factor
            }
            for ws in factory.waste_streams
        ]
    )

@router.post("/data", response_model=ActivityDataResponse)
def save_factory_data(
    id: int,
    payload: ActivityDataPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    factory = verify_factory_access(id, current_user, db)

    # Replace existing streams cleanly
    db.query(EnergySource).filter(EnergySource.factory_id == factory.id).delete()
    db.query(MaterialInput).filter(MaterialInput.factory_id == factory.id).delete()
    db.query(Process).filter(Process.factory_id == factory.id).delete()
    db.query(WasteStream).filter(WasteStream.factory_id == factory.id).delete()

    for es_in in payload.energy_sources:
        es = EnergySource(
            factory_id=factory.id,
            source_type=es_in.source_type,
            annual_consumption=es_in.annual_consumption,
            unit=es_in.unit,
            emission_factor=es_in.emission_factor,
            factor_source=es_in.factor_source
        )
        db.add(es)

    for mi_in in payload.material_inputs:
        mi = MaterialInput(
            factory_id=factory.id,
            material_type=mi_in.material_type,
            annual_quantity=mi_in.annual_quantity,
            unit=mi_in.unit,
            recycled_content_percent=mi_in.recycled_content_percent,
            emission_factor=mi_in.emission_factor
        )
        db.add(mi)

    for p_in in payload.processes:
        p = Process(
            factory_id=factory.id,
            name=p_in.name,
            equipment=p_in.equipment,
            operating_hours=p_in.operating_hours,
            primary_energy_source=p_in.primary_energy_source,
            operating_pressure_bar=p_in.operating_pressure_bar,
            estimated_leakage_percent=p_in.estimated_leakage_percent,
            annual_energy_kwh=p_in.annual_energy_kwh,
            notes=p_in.notes
        )
        db.add(p)

    for ws_in in payload.waste_streams:
        ws = WasteStream(
            factory_id=factory.id,
            waste_type=ws_in.waste_type,
            annual_quantity=ws_in.annual_quantity,
            unit=ws_in.unit,
            treatment_method=ws_in.treatment_method,
            emission_factor=ws_in.emission_factor
        )
        db.add(ws)

    db.commit()
    db.refresh(factory)
    return get_factory_data(id, current_user, db)
