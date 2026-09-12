from typing import Dict, Any, List
from app.models.factory import Factory
from app.models.hotspot import Hotspot

def diagnose_root_cause(factory: Factory, hotspot: Hotspot) -> Dict[str, Any]:
    code = hotspot.code
    grid_factor = factory.energy_sources[0].emission_factor if factory.energy_sources else 0.48

    # Match process if available
    proc = next((p for p in factory.processes if "air" in p.name.lower() or "compress" in p.name.lower()), None)
    leakage_pct = proc.estimated_leakage_percent if proc else 28.0
    pressure_bar = proc.operating_pressure_bar if proc else 7.5
    energy_kwh = proc.annual_energy_kwh if proc else 337500.0
    wasted_kwh = (energy_kwh * (leakage_pct / 100.0)) if leakage_pct > 0 else 94500.0

    if "air" in code or "compress" in code:
        return {
            "hotspot_code": "compressed-air",
            "summary_carbon": hotspot.carbon_tco2e,
            "summary_unit": f"tCO₂e · {hotspot.title}",
            "process_name": hotspot.title,
            "carbon_str": f"{round(hotspot.carbon_tco2e, 0)} tCO₂e / year",
            "signal_str": f"{int(leakage_pct)}% leakage",
            "condition_str": f"{pressure_bar} bar operating pressure",
            "root_cause_label": "Unmanaged Air Leakage & Over-pressurization",
            "root_cause_text": "Pneumatic network leakage combined with excess line header pressure.",
            "root_cause_title": "Pneumatic leakage and excessive header pressure drive avoidable motor load.",
            "root_cause_description": "The strongest diagnostic evidence indicates that electrical energy is escaping through worn fittings, push-in connectors, and neglected drain valves, while the compressor operates at higher-than-required line pressure to compensate.",
            "leakage_metric": f"{int(leakage_pct)}%",
            "wasted_metric": f"{int(wasted_kwh):,} kWh/year",
            "pressure_metric": f"{pressure_bar} bar",
            "target_metric": "~6.2 bar",
            "diagnostic_reason": "Reducing network leakage and lowering operating pressure by 1.3 bar directly reduces compressor motor loading without compromising end-use tool performance.",
            "evidence_points": [
                f"Audible and metered distribution leakage of {int(leakage_pct)}% exceeds the 10% best-practice benchmark.",
                f"System header is regulated at {pressure_bar} bar whereas terminal pneumatic actuators require only 6.0 to 6.2 bar.",
                f"Avoidable electricity wasted equals {int(wasted_kwh):,} kWh/year, representing {round((wasted_kwh * grid_factor) / 1000, 1)} tCO₂e of avoidable emissions."
            ],
            "assumptions": [
                "Screw compressor control utilizes load/unload throttling rather than full variable speed modulation.",
                "Pneumatic distribution piping has not undergone ultrasonic acoustic leak audits within the last 12 months."
            ],
            "confidence_pct": hotspot.confidence_pct
        }

    elif "cnc" in code or "machin" in code:
        cnc_proc = next((p for p in factory.processes if "cnc" in p.name.lower() or "machin" in p.name.lower()), None)
        hours = cnc_proc.operating_hours if cnc_proc else 6200.0
        kwh = cnc_proc.annual_energy_kwh if cnc_proc else 475000.0
        idle_waste = kwh * 0.28
        return {
            "hotspot_code": "cnc",
            "summary_carbon": hotspot.carbon_tco2e,
            "summary_unit": f"tCO₂e · {hotspot.title}",
            "process_name": hotspot.title,
            "carbon_str": f"{round(hotspot.carbon_tco2e, 0)} tCO₂e / year",
            "signal_str": "High idle energy load",
            "condition_str": f"{int(hours):,} operating hours",
            "root_cause_label": "Uncontrolled Machine Idle & Auxiliary Power",
            "root_cause_text": "Auxiliary pumps and spindle chillers remain fully powered during non-cutting cycles.",
            "root_cause_title": "Machine auxiliaries draw continuous base power during non-productive intervals.",
            "root_cause_description": "Telemetry and operational logs reveal that spindle chillers, hydraulic pumps, and chip conveyors remain energized during tool setups, operator changeovers, and material staging.",
            "leakage_metric": "High",
            "wasted_metric": f"~{int(idle_waste):,} kWh/year idle load",
            "pressure_metric": f"{int(hours):,} h/year",
            "target_metric": "Auto-sleep standby mode",
            "diagnostic_reason": "Implementing automated sleep state transitions after 5 minutes of idle time reduces non-productive electricity without impacting machining throughput.",
            "evidence_points": [
                f"Machine operating hours total {int(hours):,} h/year with an estimated 25-35% non-cutting idle ratio.",
                "Auxiliary lubrication, cooling, and hydraulics lack interlocked auto-shutdown timers.",
                f"Idle power consumption accounts for approximately {int(idle_waste):,} kWh/year."
            ],
            "assumptions": [
                "Machine controller supports G-code and PLC auxiliary standby triggers.",
                "Tool change intervals average 12-18 minutes between active machining runs."
            ],
            "confidence_pct": hotspot.confidence_pct
        }

    elif "alum" in code or "material" in code:
        mat = factory.material_inputs[0] if factory.material_inputs else None
        recycled = mat.recycled_content_percent if mat else 20.0
        qty = mat.annual_quantity if mat else 50000.0
        return {
            "hotspot_code": "aluminium",
            "summary_carbon": hotspot.carbon_tco2e,
            "summary_unit": f"tCO₂e · {hotspot.title}",
            "process_name": hotspot.title,
            "carbon_str": f"{round(hotspot.carbon_tco2e, 0)} tCO₂e / year",
            "signal_str": f"{int(recycled)}% recycled content",
            "condition_str": "Virgin primary smelting feedstock",
            "root_cause_label": "Virgin Feedstock Embodied Carbon Penalty",
            "root_cause_text": "Predominance of primary smelted aluminium in bill of materials.",
            "root_cause_title": "Primary virgin smelting dominates upstream Scope 3 embodied carbon.",
            "root_cause_description": "Primary smelting consumes high electrochemical energy (~14 kWh/kg), yielding 8.0 kgCO₂e/kg versus only 0.5 kgCO₂e/kg for secondary remelted aluminium.",
            "leakage_metric": f"{int(100 - recycled)}% virgin",
            "wasted_metric": f"{int(qty):,} kg annual intake",
            "pressure_metric": "8.0 kgCO₂e/kg factor",
            "target_metric": "≥60% recycled alloy blend",
            "diagnostic_reason": "Transitioning to certified secondary alloy with 60-70% recycled content cuts material footprint by ~40% without tooling alterations.",
            "evidence_points": [
                f"Current feedstock has only {int(recycled)}% verified recycled content.",
                "Virgin primary aluminium factor is 16× higher than secondary recycled ingot.",
                f"Material emissions represent {round(hotspot.share_pct)}% of total evaluated plant emissions."
            ],
            "assumptions": [
                "Component structural specifications permit standard 6061-T6 recycled blend certifications.",
                "Regional scrap and billet suppliers have validated secondary ingot availability."
            ],
            "confidence_pct": hotspot.confidence_pct
        }

    else:
        return {
            "hotspot_code": code,
            "summary_carbon": hotspot.carbon_tco2e,
            "summary_unit": f"tCO₂e · {hotspot.title}",
            "process_name": hotspot.title,
            "carbon_str": f"{round(hotspot.carbon_tco2e, 0)} tCO₂e / year",
            "signal_str": hotspot.signal_value,
            "condition_str": hotspot.operating_condition or "Normal",
            "root_cause_label": "Operational Inefficiency & Grid Intensity",
            "root_cause_text": "Continuous electrical consumption against standard fossil-heavy grid supply.",
            "root_cause_title": "Continuous utility consumption without demand optimization.",
            "root_cause_description": "Activity stream analysis indicates baseline electrical load without automated power modulation or load matching.",
            "leakage_metric": "Moderate",
            "wasted_metric": "Estimated operational loss",
            "pressure_metric": "Standard operation",
            "target_metric": "Demand optimization & solar PPA",
            "diagnostic_reason": "Targeted load management and renewable power transition provide the most reliable abatement pathway.",
            "evidence_points": [
                f"Calculated carbon baseline of {round(hotspot.carbon_tco2e, 1)} tCO₂e.",
                "Lack of sub-metered power analytics across operational shifts."
            ],
            "assumptions": [
                "Factory tariff is commercial grid industrial standard."
            ],
            "confidence_pct": hotspot.confidence_pct
        }
