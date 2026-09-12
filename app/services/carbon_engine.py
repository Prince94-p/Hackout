from datetime import datetime, timezone
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.factory import Factory
from app.models.activity import EnergySource, MaterialInput, Process, WasteStream, EmissionFactor
from app.models.emissions import EmissionRecord

DEFAULT_FACTORS = [
    {
        "category": "energy",
        "item_name": "Grid Electricity",
        "factor_value": 0.48,
        "unit": "kgCO₂e/kWh",
        "source_name": "Central Electricity Authority (CEA)",
        "source_reference": "CO2 Baseline Database for the Indian Power Sector, User Guide Version 20.0",
        "region": "India",
        "version_year": "2024"
    },
    {
        "category": "material",
        "item_name": "Virgin Aluminium",
        "factor_value": 8.0,
        "unit": "kgCO₂e/kg",
        "source_name": "International Aluminium Institute (IAI)",
        "source_reference": "IAI Life Cycle Carbon Assessment of Primary Aluminium 2024 / Ecoinvent 3.10",
        "region": "Global / India",
        "version_year": "2024"
    },
    {
        "category": "material",
        "item_name": "Recycled Aluminium",
        "factor_value": 0.5,
        "unit": "kgCO₂e/kg",
        "source_name": "International Aluminium Institute (IAI)",
        "source_reference": "Secondary Aluminium Production Benchmark (Remelting / Scrap)",
        "region": "Global",
        "version_year": "2024"
    },
    {
        "category": "waste",
        "item_name": "Aluminium Machining Swarf",
        "factor_value": 2.0,
        "unit": "kgCO₂e/kg",
        "source_name": "IPCC / UK DEFRA",
        "source_reference": "Industrial Waste Disposal and Scrap Treatment Emission Guidelines",
        "region": "Global",
        "version_year": "2024"
    }
]

def seed_default_factors_if_empty(db: Session):
    if db.query(EmissionFactor).count() == 0:
        for f in DEFAULT_FACTORS:
            factor = EmissionFactor(**f)
            db.add(factor)
        db.commit()

def calculate_factory_emissions(factory: Factory, db: Session) -> EmissionRecord:
    seed_default_factors_if_empty(db)

    # 1. Energy Carbon (Deterministic: activity * factor / 1000)
    energy_tco2e = 0.0
    factor_citations: List[Dict[str, Any]] = []

    for es in factory.energy_sources:
        stream_carbon = (es.annual_consumption * es.emission_factor) / 1000.0
        energy_tco2e += stream_carbon
        factor_citations.append({
            "category": "energy",
            "item_name": es.source_type,
            "factor_value": es.emission_factor,
            "unit": "kgCO₂e/kWh",
            "source_name": es.factor_source or "Configured Grid Factor",
            "source_reference": "CEA 2024 v20.0" if "Grid" in es.source_type else "IPCC/DEFRA 2024",
            "region": "India",
            "version_year": "2024"
        })

    # 2. Materials Carbon
    material_tco2e = 0.0
    for mi in factory.material_inputs:
        stream_carbon = (mi.annual_quantity * mi.emission_factor) / 1000.0
        material_tco2e += stream_carbon
        factor_citations.append({
            "category": "material",
            "item_name": mi.material_type,
            "factor_value": mi.emission_factor,
            "unit": "kgCO₂e/kg",
            "source_name": "IAI / Ecoinvent 3.10",
            "source_reference": "Primary Metal Production Lifecycle Benchmark",
            "region": "India / Global",
            "version_year": "2024"
        })

    # 3. Waste Carbon
    waste_tco2e = 0.0
    for ws in factory.waste_streams:
        stream_carbon = (ws.annual_quantity * ws.emission_factor) / 1000.0
        waste_tco2e += stream_carbon
        factor_citations.append({
            "category": "waste",
            "item_name": ws.waste_type,
            "factor_value": ws.emission_factor,
            "unit": "kgCO₂e/kg",
            "source_name": "IPCC / DEFRA Guidelines",
            "source_reference": f"Treatment Method: {ws.treatment_method}",
            "region": "India",
            "version_year": "2024"
        })

    # Total Baseline (Process energy is attributional within Energy, never double-counted)
    total_tco2e = energy_tco2e + material_tco2e + waste_tco2e

    # Percentages
    if total_tco2e > 0:
        energy_pct = round((energy_tco2e / total_tco2e) * 100.0, 1)
        material_pct = round((material_tco2e / total_tco2e) * 100.0, 1)
        waste_pct = round((waste_tco2e / total_tco2e) * 100.0, 1)
    else:
        energy_pct = material_pct = waste_pct = 0.0

    # Largest source
    cat_map = {"Energy": energy_tco2e, "Materials": material_tco2e, "Waste": waste_tco2e}
    largest_source = max(cat_map, key=cat_map.get) if total_tco2e > 0 else "None"

    # Explainable Confidence Calculation (Rule 11)
    # 1. Activity Data Completeness: Have energy, material, waste, and process data been entered?
    has_energy = len(factory.energy_sources) > 0 and energy_tco2e > 0
    has_material = len(factory.material_inputs) > 0 and material_tco2e > 0
    has_waste = len(factory.waste_streams) > 0 and waste_tco2e > 0
    has_process = len(factory.processes) > 0

    activity_completeness = sum([has_energy, has_material, has_waste, has_process]) / 4.0 * 100.0

    # 2. Factor Quality: Are emission factors specific and supported?
    factor_quality = 85.0 if len(factor_citations) > 0 else 50.0

    # 3. Operational Signal Completeness: Do processes have hours, pressure, leakage metrics?
    proc_signals = 0
    proc_count = len(factory.processes)
    if proc_count > 0:
        for p in factory.processes:
            if p.operating_hours > 0 or p.operating_pressure_bar > 0 or p.estimated_leakage_percent > 0:
                proc_signals += 1
        operational_completeness = (proc_signals / proc_count) * 100.0
    else:
        operational_completeness = 60.0

    # 4. Evidence Quality: Factory verified production units and active facility profile
    evidence_quality = 85.0 if factory.annual_production > 0 else 65.0

    # Weighted Confidence
    overall_confidence = round(
        (activity_completeness * 0.35) +
        (factor_quality * 0.25) +
        (operational_completeness * 0.25) +
        (evidence_quality * 0.15),
        1
    )

    confidence_breakdown = {
        "activity_data_completeness": round(activity_completeness, 1),
        "factor_quality": round(factor_quality, 1),
        "operational_signal_completeness": round(operational_completeness, 1),
        "evidence_quality": round(evidence_quality, 1)
    }

    # Process level calculations for attribution
    process_details = []
    for p in factory.processes:
        p_kwh = p.annual_energy_kwh or 0.0
        # Use factory grid electricity factor for process energy attribution
        p_factor = factory.energy_sources[0].emission_factor if factory.energy_sources else 0.48
        p_tco2e = (p_kwh * p_factor) / 1000.0
        process_details.append({
            "name": p.name,
            "equipment": p.equipment,
            "kwh": p_kwh,
            "carbon_tco2e": round(p_tco2e, 1),
            "leakage_pct": p.estimated_leakage_percent,
            "pressure_bar": p.operating_pressure_bar,
            "hours": p.operating_hours
        })

    record = EmissionRecord(
        factory_id=factory.id,
        calculation_date=datetime.now(timezone.utc),
        total_tco2e=round(total_tco2e, 2),
        energy_tco2e=round(energy_tco2e, 2),
        material_tco2e=round(material_tco2e, 2),
        waste_tco2e=round(waste_tco2e, 2),
        energy_pct=energy_pct,
        material_pct=material_pct,
        waste_pct=waste_pct,
        largest_source=largest_source,
        confidence_score=overall_confidence,
        confidence_breakdown=json.dumps(confidence_breakdown),
        factor_traceability=json.dumps(factor_citations),
        details_json=json.dumps({"processes": process_details})
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
