import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.factory import Factory
from app.models.hotspot import Hotspot

def evaluate_and_generate_hotspots(factory: Factory, db: Session) -> List[Hotspot]:
    grid_factor = factory.energy_sources[0].emission_factor if factory.energy_sources else 0.48
    processes = factory.processes
    candidates: List[Dict[str, Any]] = []

    # 1. Process candidate evaluation
    for p in processes:
        p_kwh = p.annual_energy_kwh or 0.0
        p_carbon = (p_kwh * grid_factor) / 1000.0
        leak = p.estimated_leakage_percent or 0.0
        press = p.operating_pressure_bar or 0.0
        hours = p.operating_hours or 0.0

        p_name_lower = p.name.lower()
        if "air" in p_name_lower or "compress" in p_name_lower:
            candidates.append({
                "code": "compressed-air",
                "title": p.name,
                "category": "Energy",
                "branch_path": "Energy → Utilities → Compressed Air",
                "carbon_tco2e": round(p_carbon, 1),
                "signal_type": "Leakage Rate",
                "signal_value": f"{int(leak)}% leakage" if leak > 0 else "Optimal",
                "operating_condition": f"{press} bar operating pressure" if press > 0 else "Normal pressure",
                "confidence_pct": 88.0,
                "details": {
                    "energy_str": f"{int(p_kwh):,} kWh",
                    "reason": "High distribution leakage combined with elevated header pressure indicates electricity is being consumed without useful production work.",
                    "intervention": "Compressor Optimization + Leak Remediation",
                    "intervention_text": "Repair leakage points, reduce line pressure to 6.2 bar, and optimize compressor sequencing."
                },
                "severity_score": p_carbon * (1.0 + (leak / 50.0))
            })
        elif "cnc" in p_name_lower or "machin" in p_name_lower:
            candidates.append({
                "code": "cnc",
                "title": p.name,
                "category": "Energy",
                "branch_path": "Energy → Production → CNC Machining",
                "carbon_tco2e": round(p_carbon, 1),
                "signal_type": "Auxiliary Idle Load",
                "signal_value": "High idle load",
                "operating_condition": f"{int(hours):,} h/year",
                "confidence_pct": 81.0,
                "details": {
                    "energy_str": f"{int(p_kwh):,} kWh",
                    "reason": "Spindle cooling and hydraulic circuits remain energized during tool changes, setups, and batch transitions, creating avoidable non-productive power demand.",
                    "intervention": "Idle Energy Control & FEMS",
                    "intervention_text": "Introduce automated sleep timers, machine-level power monitoring, and production cycle synchronization."
                },
                "severity_score": p_carbon * 1.15
            })
        elif "heat" in p_name_lower or "furnace" in p_name_lower:
            candidates.append({
                "code": "heat-treatment",
                "title": p.name,
                "category": "Energy",
                "branch_path": "Energy → Thermal → Heat Treatment",
                "carbon_tco2e": round(p_carbon, 1),
                "signal_type": "Exhaust Heat Loss",
                "signal_value": "Thermal loss",
                "operating_condition": "High furnace load",
                "confidence_pct": 76.0,
                "details": {
                    "energy_str": f"{int(p_kwh):,} kWh",
                    "reason": "Repeated heating cycles and convective heat loss through exhaust flues increase overall thermal electricity demand.",
                    "intervention": "Waste Heat Recovery",
                    "intervention_text": "Capture flue gas thermal energy for preheating and install ceramic radiation insulation."
                },
                "severity_score": p_carbon * 1.1
            })
        else:
            candidates.append({
                "code": f"process-{p.id}",
                "title": p.name,
                "category": "Energy",
                "branch_path": f"Energy → Production → {p.name}",
                "carbon_tco2e": round(p_carbon, 1),
                "signal_type": "Process Energy",
                "signal_value": f"{int(p_kwh):,} kWh",
                "operating_condition": f"{int(hours):,} h/year",
                "confidence_pct": 75.0,
                "details": {
                    "energy_str": f"{int(p_kwh):,} kWh",
                    "reason": "Continuous electrical loading without variable speed control.",
                    "intervention": "Motor & Drive Efficiency Upgrade",
                    "intervention_text": "Upgrade to IE4 motors with variable frequency drives."
                },
                "severity_score": p_carbon
            })

    # 2. Material input candidates
    for m in factory.material_inputs:
        m_carbon = (m.annual_quantity * m.emission_factor) / 1000.0
        recycled = m.recycled_content_percent or 0.0
        candidates.append({
            "code": "aluminium" if "alum" in m.material_type.lower() else f"material-{m.id}",
            "title": m.material_type,
            "category": "Materials",
            "branch_path": f"Materials → Feedstock → {m.material_type}",
            "carbon_tco2e": round(m_carbon, 1),
            "signal_type": "Virgin Content Share",
            "signal_value": f"{int(recycled)}% recycled",
            "operating_condition": f"{int(m.annual_quantity):,} kg/year",
            "confidence_pct": 82.0,
            "details": {
                "energy_str": f"{int(m.annual_quantity):,} kg",
                "reason": f"Feedstock contains {int(100 - recycled)}% virgin material. Virgin smelting creates high embodied emissions compared to secondary remelting.",
                "intervention": "Increase Recycled Feedstock Blend",
                "intervention_text": f"Qualify secondary alloys with suppliers to increase recycled content to ≥60%."
            },
            "severity_score": m_carbon * (1.0 + (100.0 - recycled) / 100.0)
        })

    # 3. Waste candidates
    for w in factory.waste_streams:
        w_carbon = (w.annual_quantity * w.emission_factor) / 1000.0
        candidates.append({
            "code": f"waste-{w.id}",
            "title": w.waste_type,
            "category": "Waste",
            "branch_path": f"Waste → Scrap → {w.waste_type}",
            "carbon_tco2e": round(w_carbon, 1),
            "signal_type": "Disposal Route",
            "signal_value": w.treatment_method,
            "operating_condition": f"{int(w.annual_quantity):,} kg/year",
            "confidence_pct": 78.0,
            "details": {
                "energy_str": f"{int(w.annual_quantity):,} kg",
                "reason": "Offsite disposal without closed-loop scrap briquetting results in material and embodied carbon loss.",
                "intervention": "Closed-Loop Scrap Briquetting",
                "intervention_text": "Briquette clean machining swarf onsite and reintroduce into secondary remelting."
            },
            "severity_score": w_carbon * 1.2
        })

    # Sort candidates by calculated severity
    candidates.sort(key=lambda x: x["severity_score"], reverse=True)

    # Calculate total carbon for share percentage
    total_carbon = sum(c["carbon_tco2e"] for c in candidates) or 1.0

    # Persist or update Hotspot records
    db.query(Hotspot).filter(Hotspot.factory_id == factory.id).delete()
    hotspots: List[Hotspot] = []

    for rank, item in enumerate(candidates[:5], start=1):
        share_pct = round((item["carbon_tco2e"] / total_carbon) * 100.0, 1)
        h = Hotspot(
            factory_id=factory.id,
            rank=rank,
            code=item["code"],
            title=item["title"],
            category=item["category"],
            branch_path=item["branch_path"],
            carbon_tco2e=item["carbon_tco2e"],
            share_pct=share_pct,
            signal_type=item["signal_type"],
            signal_value=item["signal_value"],
            operating_condition=item["operating_condition"],
            confidence_pct=item["confidence_pct"],
            details_json=json.dumps(item["details"])
        )
        db.add(h)
        hotspots.append(h)

    db.commit()
    return hotspots
