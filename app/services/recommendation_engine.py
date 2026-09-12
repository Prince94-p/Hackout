import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.factory import Factory
from app.models.recommendation import Recommendation
from app.models.emissions import EmissionRecord

INTERVENTIONS_CATALOG = [
    {
        "code": "compressor",
        "title": "Compressor Optimization & Leak Remediation",
        "description": "Repair compressed-air distribution leaks, reduce discharge header pressure to 6.2 bar, and optimize compressor sequencing to remove avoidable electricity demand.",
        "category": "Utility Optimization",
        "target_process": "Compressed Air",
        "root_cause": "28% Leakage & Over-pressurization",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "15-25% utility energy",
        "cost_range": "₹1.0L - ₹2.5L",
        "requirements": "Ultrasonic leak audit, pressure regulator calibration",
        "assumption_reference": "Compressed Air Challenge (CAC) Best Practices Benchmark: 1.3 bar reduction cuts 9% power draw; leak reduction from 28% to 10% saves 18% base load.",
        "justification": "Targets confirmed avoidable pneumatic loss with low capital outlay and rapid payback without altering factory throughput."
    },
    {
        "code": "ultrasonic_leaks",
        "title": "Ultrasonic Leak Detection & Scheduled Remediation",
        "description": "Establish a bi-monthly ultrasonic leak-tagging program across plant air headers, quick-connects, and pneumatic tools.",
        "category": "Maintenance Protocol",
        "target_process": "Compressed Air Lines",
        "root_cause": "Unchecked Piping Deterioration",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "8-14% compressor power",
        "cost_range": "₹0.6L - ₹1.2L",
        "requirements": "Ultrasonic acoustic sensor equipment, maintenance logging",
        "assumption_reference": "US DOE Compressed Air Tip Sheet #3: Sustained ultrasonic leak tagging maintains air leakage below 10% versus unmanaged 30%.",
        "justification": "Low-cost preventive protocol ensuring distribution network does not silently degrade back into leakage."
    },
    {
        "code": "aluminium",
        "title": "Increase Recycled Aluminium Share",
        "description": "Increase certified recycled-content billet share in foundry feedstock to displace virgin primary Hall-Héroult aluminium.",
        "category": "Circular Materials",
        "target_process": "Material Inputs",
        "root_cause": "High Virgin Share (80%)",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "30-50% material carbon",
        "cost_range": "₹3.0L - ₹6.0L",
        "requirements": "Alloy chemistry certification, supplier qualification",
        "assumption_reference": "IAI Lifecycle Aluminium Report: Secondary remelting consumes 95% less energy than primary smelting (0.5 kgCO₂e/kg vs 8.0 kgCO₂e/kg).",
        "justification": "Yields the largest absolute Scope 3 footprint reduction through supplier qualification of secondary ingot blends."
    },
    {
        "code": "heat",
        "title": "Waste Heat Recovery (Flue Gas Recuperator)",
        "description": "Recover usable thermal energy from annealing furnaces and exhaust flues to preheat combustion air or process wash baths.",
        "category": "Thermal Efficiency",
        "target_process": "Heat Treatment",
        "root_cause": "Unrecovered Exhaust Heat",
        "effort_level": "High",
        "disruption_level": "Medium",
        "derivation_type": "benchmark-based",
        "saving_range": "18-25% thermal demand",
        "cost_range": "₹4.5L - ₹9.0L",
        "requirements": "Heat exchanger retrofit, exhaust temperature monitoring",
        "assumption_reference": "Bureau of Energy Efficiency (BEE) Thermal Process Benchmark: Flue gas recuperation yields 18-24% heat input displacement.",
        "justification": "Captures high-temperature exhaust gas to preheat incoming combustion air or tooling baskets."
    },
    {
        "code": "renewable",
        "title": "Onsite Rooftop Solar & Renewable PPA Transition",
        "description": "Install rooftop solar PV and subscribe to open-access green tariffs to displace high-carbon commercial grid electricity.",
        "category": "Clean Energy",
        "target_process": "Grid Electricity",
        "root_cause": "Grid Carbon Intensity",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "20-35% Scope 2 carbon",
        "cost_range": "₹12.0L - ₹25.0L",
        "requirements": "Roof structural assessment, net-metering approval",
        "assumption_reference": "MNRE Rooftop Solar Model: 100 kWp onsite solar array generates ~145,000 kWh/year at zero Scope 2 emissions.",
        "justification": "Displaces high-carbon grid supply directly at factory busbars with predictable long-term levelized tariff."
    },
    {
        "code": "idle_cnc",
        "title": "Automatic Idle Machine Shutdown & FEMS Interlocks",
        "description": "Install programmable power-down relays and auxiliary sleep interlocks on CNC machining spindles, hydraulics, and chip augers.",
        "category": "Production Optimization",
        "target_process": "CNC Machining",
        "root_cause": "Auxiliary Idle Energy",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "15-25% machining energy",
        "cost_range": "₹1.2L - ₹2.0L",
        "requirements": "PLC programming, sleep state delay relays",
        "assumption_reference": "Fraunhofer Machine Tool Idle Study: Standby power accounts for 25-30% of total electrical consumption during non-cutting shifts.",
        "justification": "Eliminates parasitic standby consumption during tool changes and batch setups with programmable logic triggers."
    },
    {
        "code": "vfd_motors",
        "title": "IE4 Super-Premium Motors & VFD Retrofits",
        "description": "Replace aged IE2 induction motors on pumps, blowers, and hydraulic power packs with IE4 permanent-magnet motors and variable speed drives.",
        "category": "Electrical Drive Efficiency",
        "target_process": "Production Drives",
        "root_cause": "Constant Speed Throttling",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "12-20% drive energy",
        "cost_range": "₹2.5L - ₹5.0L",
        "requirements": "VFD panel enclosure, harmonic choke installation",
        "assumption_reference": "IEC 60034-30-1 Motor Standards: IE4 efficiency achieves 96.2% efficiency versus 89% for older standard motors.",
        "justification": "Dynamically modulates motor speeds to match fluctuating production pressure and flow requirements."
    },
    {
        "code": "vsd_compressor",
        "title": "Variable Speed Drive (VSD) Compressor Retrofit",
        "description": "Replace fixed-speed trim compressor with an inverter-driven variable speed rotary screw compressor to match factory demand variations.",
        "category": "Compressed Air",
        "target_process": "Compressed Air System",
        "root_cause": "Unloaded Compressor Blow-off",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "15-28% trim air power",
        "cost_range": "₹5.0L - ₹8.5L",
        "requirements": "VSD compressor skid installation, master controller link",
        "assumption_reference": "CAGI Compressor Verification Data: VSD compressors maintain flat specific power down to 25% turndown versus 70% power waste at idle.",
        "justification": "Eliminates unloaded bypass blow-off and cycling losses during fluctuating manufacturing shifts."
    },
    {
        "code": "smart_air",
        "title": "Smart Pressure Monitoring & Dual-Setpoints",
        "description": "Deploy permanent thermal mass flow meters and digital pressure transducers to implement zoned dual-setpoint pressure regulation.",
        "category": "Digital Monitoring",
        "target_process": "Compressed Air",
        "root_cause": "Over-pressurized Trunk Headers",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "6-10% air energy",
        "cost_range": "₹0.8L - ₹1.8L",
        "requirements": "Digital pressure transducers, SCADA IoT gateway",
        "assumption_reference": "ISO 11011 Compressed Air Energy Efficiency Standard: 1 bar reduction reduces pneumatic tool electrical consumption by 7%.",
        "justification": "Maintains persistent air system tightness and alerts operators before leak rates exceed 10% threshold."
    },
    {
        "code": "briquetting",
        "title": "Onsite Swarf Briquetting & Closed-Loop Remelting",
        "description": "Compress loose aluminium/steel turnings into solid high-density briquettes onsite, removing residual cutting fluid and eliminating scrap oxidation.",
        "category": "Waste Valorization",
        "target_process": "Waste Streams",
        "root_cause": "Scrap Oxidation & Landfill Loss",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "35-50% scrap footprint",
        "cost_range": "₹3.5L - ₹7.0L",
        "requirements": "Hydraulic briquetting press, cutting oil separator",
        "assumption_reference": "European Aluminium Circularity Guide: Briquetted chips exhibit <2% melt loss versus 15% for loose chips, capturing full material value.",
        "justification": "Transforms low-value machining waste into high-purity melting stock for closed-loop secondary ingot manufacture."
    },
    {
        "code": "scrap_loop",
        "title": "Scrap Recycling Loop & Direct Foundry Return",
        "description": "Establish a dedicated closed-loop return pipeline with regional certified smelters for off-spec trimmings and gate runners.",
        "category": "Circular Value",
        "target_process": "Metal Scrap",
        "root_cause": "Open-Loop Scrap Degradation",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "20-30% Scope 3 waste carbon",
        "cost_range": "₹1.5L - ₹3.0L",
        "requirements": "Tote segregation, buyback contract with partner smelter",
        "assumption_reference": "Ellen MacArthur Foundation Industrial Circularity: Closed-loop metallurgical returns cut 85% embodied energy vs open-market scrap downgrade.",
        "justification": "Eliminates downcycling of high-grade alloy scrap into inferior alloys."
    },
    {
        "code": "mat_sub",
        "title": "Material Substitution (Low-Carbon Alloy Specification)",
        "description": "Qualify lower-embodied-carbon secondary alloy specifications for non-structural housings and brackets.",
        "category": "Material Engineering",
        "target_process": "Component Feedstock",
        "root_cause": "Over-specified Virgin Purity",
        "effort_level": "Medium",
        "disruption_level": "Medium",
        "derivation_type": "benchmark-based",
        "saving_range": "15-28% feedstock carbon",
        "cost_range": "₹2.0L - ₹4.5L",
        "requirements": "Mechanical tensile and fatigue validation, customer signoff",
        "assumption_reference": "ASM International Materials Handbook: Low-carbon remelt alloys match mechanical specifications for 70% of automotive housings.",
        "justification": "Permanently reduces baseline product footprint without adding ongoing operational costs."
    },
    {
        "code": "thermal_insulation",
        "title": "Thermal Insulation Upgrade (Ceramic Fiber Linings)",
        "description": "Re-line furnace doors, reheat flues, and hot transfer piping with high-density ceramic fiber refractory modules.",
        "category": "Thermal Conservation",
        "target_process": "Furnaces & Reheaters",
        "root_cause": "Convective & Radiation Wall Loss",
        "effort_level": "Medium",
        "disruption_level": "Medium",
        "derivation_type": "benchmark-based",
        "saving_range": "10-18% furnace fuel",
        "cost_range": "₹1.8L - ₹3.5L",
        "requirements": "Thermographic survey, weekend shutdown for refractory re-lining",
        "assumption_reference": "BEE Furnace Insulation Code: Surface temperature reduction from 120°C to 55°C saves 14% fuel input.",
        "justification": "Immediate thermal barrier restoration requiring zero operational retraining."
    },
    {
        "code": "mql_machining",
        "title": "Minimum Quantity Lubrication (MQL) / Dry Machining",
        "description": "Transition high-speed milling lines from flood coolant to aerosolized Minimum Quantity Lubrication (MQL) with vegetable ester base.",
        "category": "Process Green Chemistry",
        "target_process": "Machining Centers",
        "root_cause": "Hazardous Coolant Disposal & Chiller Load",
        "effort_level": "Medium",
        "disruption_level": "Medium",
        "derivation_type": "benchmark-based",
        "saving_range": "8-15% machining power + 80% coolant waste",
        "cost_range": "₹2.5L - ₹5.0L",
        "requirements": "MQL micro-dosing pump nozzle kits, coated carbide tooling",
        "assumption_reference": "CIRP Annals on Sustainable Machining: MQL cuts coolant lifecycle emissions by 82% while eliminating centralized pump tanks.",
        "justification": "Radically reduces toxic coolant mist, wastewater disposal, and auxiliary pump electrical loading."
    },
    {
        "code": "fems",
        "title": "Factory Energy Management System (ISO 50001 FEMS)",
        "description": "Deploy comprehensive cloud-connected digital IoT power meters on all machine feeders with automated anomaly alerting.",
        "category": "Enterprise Monitoring",
        "target_process": "Plant-wide Power Distribution",
        "root_cause": "Unmetered Off-Shift Baseload",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "6-12% total facility power",
        "cost_range": "₹2.2L - ₹4.2L",
        "requirements": "Multifunction meters, Modbus/TCP gateways, analytics portal",
        "assumption_reference": "ISO 50001 Energy Management Case Studies: Sub-metering visibility achieves 8% sustained energy reduction within 12 months.",
        "justification": "Empowers plant engineers to identify unmonitored baseline creep and peak tariff penalties."
    },
    {
        "code": "water_reuse",
        "title": "Process Water Closed-Loop Filtration & Reuse",
        "description": "Install micro-filtration and oil-skimming recovery on component washing lines to establish a 90% closed water circulation loop.",
        "category": "Water & Effluent",
        "target_process": "Parts Washing & Quenching",
        "root_cause": "Once-Through Wash Water Drain",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "75-90% freshwater intake",
        "cost_range": "₹1.8L - ₹3.8L",
        "requirements": "Hydrocyclone oil separator, cartridge polishing filters",
        "assumption_reference": "CPCB Cleaner Production Guidelines: Closed-loop parts washing conserves water and prevents sludge carbon emissions.",
        "justification": "Preserves municipal water allocations and minimizes industrial wastewater treatment discharge."
    },
    {
        "code": "steam_condensate",
        "title": "Condensate Steam Heat Recovery",
        "description": "Insulate steam lines and return high-temperature condensate back to boiler feedwater tank via pressurized return pump.",
        "category": "Steam & Boiler",
        "target_process": "Boiler & Steam Utility",
        "root_cause": "Flashing Condensate Loss",
        "effort_level": "Medium",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "10-15% boiler fuel",
        "cost_range": "₹1.5L - ₹3.2L",
        "requirements": "Steam trap inspection, thermodynamic condensate pump skid",
        "assumption_reference": "Spirax Sarco Energy Handbook: Every 6°C rise in boiler feedwater temperature reduces fuel consumption by 1%.",
        "justification": "Maximizes enthalpy recovery from already-treated demineralized boiler water."
    },
    {
        "code": "power_factor",
        "title": "Active Power Factor Correction (APFC) Panel",
        "description": "Install micro-processor controlled thyristor-switched capacitor banks to maintain factory power factor at 0.99 lagging.",
        "category": "Electrical Quality",
        "target_process": "Main Transformer Substation",
        "root_cause": "Inductive Reactive Power Loss",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "3-6% transformer loss",
        "cost_range": "₹1.2L - ₹2.5L",
        "requirements": "APFC controller, detuned reactor banks",
        "assumption_reference": "CEA Power Quality Guidelines: Upgrading PF from 0.88 to 0.99 eliminates utility penalty and cuts I²R distribution losses.",
        "justification": "Direct reduction in distribution cable heating and electrical utility maximum demand charges."
    },
    {
        "code": "led_lighting",
        "title": "High-Efficiency LED High-Bay Lighting with Daylighting",
        "description": "Replace metal halide high bays with 160 lm/W smart LED fixtures coupled to skylight photocells and occupancy microwave sensors.",
        "category": "Facility Utilities",
        "target_process": "Plant Illumination",
        "root_cause": "Legacy 400W Metal Halide Fixtures",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "calculated",
        "saving_range": "50-65% lighting load",
        "cost_range": "₹0.9L - ₹1.8L",
        "requirements": "High-bay mounting brackets, daylight sensors",
        "assumption_reference": "BEE Star Label Industrial Lighting Standards: Smart LED retrofits cut lighting power density from 12 W/m² to 4 W/m².",
        "justification": "Reliable quick-win electricity reduction requiring zero production downtime."
    },
    {
        "code": "coolant_filtration",
        "title": "Coolant Recycling & Centrifugal Oil-Separator Loop",
        "description": "Deploy mobile high-speed disk centrifuge to strip tramp oils and fine particulate from water-miscible metalworking fluid, extending sump life.",
        "category": "Circular Fluids",
        "target_process": "Machining Fluid Sumps",
        "root_cause": "Premature Sump Dumping",
        "effort_level": "Low",
        "disruption_level": "Low",
        "derivation_type": "benchmark-based",
        "saving_range": "60-75% coolant concentrate consumption",
        "cost_range": "₹1.4L - ₹2.8L",
        "requirements": "Mobile centrifugal separator unit, refractometer calibration",
        "assumption_reference": "SME Manufacturing Fluid Best Practices: Tramp oil removal extends emulsion life from 3 months to over 24 months.",
        "justification": "Drastically reduces recurring bio-chemical purchasing and hazardous chemical incineration footprint."
    }
]

def generate_factory_recommendations(factory: Factory, db: Session) -> List[Recommendation]:
    grid_factor = factory.energy_sources[0].emission_factor if factory.energy_sources else 0.48
    rec = db.query(EmissionRecord).filter(EmissionRecord.factory_id == factory.id).order_by(EmissionRecord.calculation_date.desc()).first()
    baseline = rec.total_tco2e if rec else 1150.0

    # Clear prior recommendations
    db.query(Recommendation).filter(Recommendation.factory_id == factory.id).delete()
    db.commit()

    recommendations: List[Recommendation] = []

    # If demo factory: reproduce exact known verified demo values
    if factory.is_demo:
        demo_specs = [
            {
                "code": "compressor",
                "title": "Compressor Optimization & Leak Remediation",
                "description": "Repair compressed-air leaks, lower operating pressure where technically feasible, and optimize compressor sequencing to remove avoidable electricity demand.",
                "category": "Utility Optimization",
                "target_process": "Compressed Air",
                "root_cause": "28% Leakage",
                "saving": 74.0,
                "cost": 1.6,
                "payback": 3.4,
                "effort": "Low",
                "reduction": 6.4,
                "confidence": 88.0,
                "disruption": "Low",
                "ref": "ISO 11011 Compressed Air Audit / 1.3 bar reduction + leak remediation benchmark",
                "derivation": "calculated",
                "justification": "It targets a confirmed avoidable loss, requires relatively low implementation effort, and can reduce carbon without reducing factory output."
            },
            {
                "code": "aluminium",
                "title": "Increase Recycled Aluminium Share",
                "description": "Increase recycled content in aluminium feedstock to reduce embodied carbon associated with virgin material production.",
                "category": "Circular Materials",
                "target_process": "Material Inputs",
                "root_cause": "High Virgin Share",
                "saving": 105.0,
                "cost": 3.8,
                "payback": 8.1,
                "effort": "Medium",
                "reduction": 9.1,
                "confidence": 82.0,
                "disruption": "Low",
                "ref": "IAI 2024 Benchmark: Secondary remelt emission factor 0.5 kgCO₂e/kg vs 8.0 kgCO₂e/kg virgin",
                "derivation": "calculated",
                "justification": "This intervention offers the largest estimated absolute carbon saving by increasing recycled content from 20% to 48%."
            },
            {
                "code": "heat",
                "title": "Waste Heat Recovery",
                "description": "Recover usable thermal energy from heat-treatment operations and reuse it for preheating or other process requirements.",
                "category": "Thermal Efficiency",
                "target_process": "Heat Treatment",
                "root_cause": "Unrecovered Heat",
                "saving": 62.0,
                "cost": 6.2,
                "payback": 14.0,
                "effort": "High",
                "reduction": 5.4,
                "confidence": 76.0,
                "disruption": "Medium",
                "ref": "BEE Industrial Energy Efficiency Guidelines / Flue Gas Heat Exchanger",
                "derivation": "benchmark-based",
                "justification": "The intervention can reduce repeated heating demand through radiant exhaust heat capture."
            },
            {
                "code": "renewable",
                "title": "Renewable Electricity Transition",
                "description": "Replace part of purchased grid electricity with lower-carbon renewable electricity through onsite rooftop solar or contracted green tariff supply.",
                "category": "Clean Energy",
                "target_process": "Grid Electricity",
                "root_cause": "Grid Carbon Intensity",
                "saving": 92.0,
                "cost": 8.5,
                "payback": 22.0,
                "effort": "Medium",
                "reduction": 8.0,
                "confidence": 71.0,
                "disruption": "Low",
                "ref": "120 kWp Solar PV Rooftop Feasibility Study (CEA Factor 0.48 kgCO₂e/kWh displacement)",
                "derivation": "calculated",
                "justification": "Renewable electricity significantly lowers Scope 2 emissions without disrupting factory mechanical operations."
            }
        ]

        for s in demo_specs:
            r = Recommendation(
                factory_id=factory.id,
                code=s["code"],
                title=s["title"],
                description=s["description"],
                category=s["category"],
                target_process=s["target_process"],
                root_cause=s["root_cause"],
                carbon_saving_tco2e=s["saving"],
                reduction_pct=s["reduction"],
                estimated_cost_inr_lakhs=s["cost"],
                payback_months=s["payback"],
                effort_level=s["effort"],
                confidence_pct=s["confidence"],
                disruption_level=s["disruption"],
                assumption_reference=s["ref"],
                derivation_type=s["derivation"],
                justification=s["justification"]
            )
            db.add(r)
            recommendations.append(r)

        db.commit()
        return recommendations

    # Normal factory: calculate deterministically from actual factory data
    total_base = baseline if baseline > 0 else 1.0

    # 1. Process / Compressed Air
    air = next((p for p in factory.processes if "air" in p.name.lower() or "compress" in p.name.lower()), None)
    if air:
        leak = air.estimated_leakage_percent or 20.0
        press = air.operating_pressure_bar or 7.0
        kwh = air.annual_energy_kwh or 200000.0
        # Leak reduction to 10% + pressure drop of (press - 6.2) * 7%
        leak_saving_kwh = kwh * (max(0.0, leak - 10.0) / 100.0)
        press_saving_kwh = kwh * (max(0.0, press - 6.2) * 0.07)
        tot_kwh = (leak_saving_kwh + press_saving_kwh) * 0.9
        saving = round((tot_kwh * grid_factor) / 1000.0, 1)
        cost = round(1.2 + (saving * 0.012), 1)
        payback = round((cost * 100000.0) / max(1000.0, (tot_kwh * 8.5) / 12.0), 1)
        red_pct = round((saving / total_base) * 100.0, 1)

        r = Recommendation(
            factory_id=factory.id,
            code="compressor",
            title="Compressor Optimization & Leak Remediation",
            description="Repair compressed-air leaks, reduce operating header pressure, and install smart sequencing.",
            category="Utility Optimization",
            target_process=air.name,
            root_cause=f"{int(leak)}% Leakage & Elevated Pressure",
            carbon_saving_tco2e=saving,
            reduction_pct=red_pct,
            estimated_cost_inr_lakhs=cost,
            payback_months=payback,
            effort_level="Low",
            confidence_pct=88.0,
            disruption_level="Low",
            assumption_reference=f"CAC Benchmark: {int(leak - 10)}% leak reduction + {round(max(0, press - 6.2), 1)} bar regulation across {int(kwh):,} kWh.",
            derivation_type="calculated",
            justification="Targets immediate avoidable electrical leakage with fast capital payback."
        )
        db.add(r)
        recommendations.append(r)

    # 2. Material Recycled Content
    if factory.material_inputs:
        mat = factory.material_inputs[0]
        cur_rec = mat.recycled_content_percent or 0.0
        target_rec = min(80.0, cur_rec + 30.0)
        delta_pct = (target_rec - cur_rec) / 100.0
        mat_saving = round((mat.annual_quantity * (mat.emission_factor - 0.5) * delta_pct) / 1000.0, 1)
        mat_cost = round(2.0 + (mat_saving * 0.02), 1)
        mat_payback = round((mat_cost * 100000.0) / max(1000.0, (mat_saving * 12000.0) / 12.0), 1)
        mat_red = round((mat_saving / total_base) * 100.0, 1)

        r = Recommendation(
            factory_id=factory.id,
            code="material_recycled",
            title=f"Increase Recycled {mat.material_type} Share",
            description=f"Qualify suppliers to increase certified recycled blend from {int(cur_rec)}% to {int(target_rec)}%.",
            category="Circular Materials",
            target_process=mat.material_type,
            root_cause=f"High Virgin Share ({int(100 - cur_rec)}%)",
            carbon_saving_tco2e=mat_saving,
            reduction_pct=mat_red,
            estimated_cost_inr_lakhs=mat_cost,
            payback_months=mat_payback,
            effort_level="Medium",
            confidence_pct=82.0,
            disruption_level="Low",
            assumption_reference=f"Material Lifecycle Study: {int(delta_pct * 100)}% recycled content increment on {int(mat.annual_quantity):,} kg feedstock.",
            derivation_type="calculated",
            justification="Abates embodied upstream Scope 3 carbon through certified recycled billets."
        )
        db.add(r)
        recommendations.append(r)

    # 3. Energy / Renewable solar
    if factory.energy_sources:
        es = factory.energy_sources[0]
        solar_displace = es.annual_consumption * 0.20
        ren_saving = round((solar_displace * es.emission_factor) / 1000.0, 1)
        ren_cost = round(5.0 + (ren_saving * 0.04), 1)
        ren_payback = round((ren_cost * 100000.0) / max(1000.0, (solar_displace * 8.5) / 12.0), 1)
        ren_red = round((ren_saving / total_base) * 100.0, 1)

        r = Recommendation(
            factory_id=factory.id,
            code="renewable",
            title="Onsite Rooftop Solar PV Transition",
            description="Install rooftop solar PV to displace 20% of commercial grid electricity with zero-emission generation.",
            category="Clean Energy",
            target_process=es.source_type,
            root_cause="Grid Carbon Intensity",
            carbon_saving_tco2e=ren_saving,
            reduction_pct=ren_red,
            estimated_cost_inr_lakhs=ren_cost,
            payback_months=ren_payback,
            effort_level="Medium",
            confidence_pct=78.0,
            disruption_level="Low",
            assumption_reference=f"Displaces {int(solar_displace):,} kWh grid power against {es.emission_factor} kgCO₂e/kWh.",
            derivation_type="calculated",
            justification="Provides reliable Scope 2 abatement with guaranteed asset life exceeding 20 years."
        )
        db.add(r)
        recommendations.append(r)

    # 4. Production CNC / Idle Shutdown
    cnc = next((p for p in factory.processes if "cnc" in p.name.lower() or "machin" in p.name.lower()), None)
    if cnc:
        kwh = cnc.annual_energy_kwh or 150000.0
        idle_saving_kwh = kwh * 0.22
        cnc_saving = round((idle_saving_kwh * grid_factor) / 1000.0, 1)
        cnc_cost = round(1.5 + (cnc_saving * 0.015), 1)
        cnc_payback = round((cnc_cost * 100000.0) / max(1000.0, (idle_saving_kwh * 8.5) / 12.0), 1)
        cnc_red = round((cnc_saving / total_base) * 100.0, 1)

        r = Recommendation(
            factory_id=factory.id,
            code="idle_cnc",
            title="Automatic Machine Sleep Interlocks & FEMS",
            description="Interlock auxiliary chillers, hydraulics, and lighting with CNC controller standby states.",
            category="Production Optimization",
            target_process=cnc.name,
            root_cause="Auxiliary Idle Power",
            carbon_saving_tco2e=cnc_saving,
            reduction_pct=cnc_red,
            estimated_cost_inr_lakhs=cnc_cost,
            payback_months=cnc_payback,
            effort_level="Low",
            confidence_pct=84.0,
            disruption_level="Low",
            assumption_reference=f"22% non-cutting idle energy reduction across {int(kwh):,} kWh.",
            derivation_type="calculated",
            justification="Cuts parasitic non-cutting energy with minimal control firmware modification."
        )
        db.add(r)
        recommendations.append(r)

    if not recommendations and baseline > 0:
        gen_saving = round(baseline * 0.08, 1)
        r = Recommendation(
            factory_id=factory.id,
            code="fems_optimization",
            title="Factory Energy Management System (FEMS) & Submetering",
            description="Install digital IoT sub-meters and automated demand monitoring across all production circuits.",
            category="Energy Efficiency",
            target_process="Main Plant Feeder",
            root_cause="Unmonitored Peak Demand",
            carbon_saving_tco2e=gen_saving,
            reduction_pct=8.0,
            estimated_cost_inr_lakhs=2.5,
            payback_months=6.0,
            effort_level="Low",
            confidence_pct=80.0,
            disruption_level="Low",
            assumption_reference="BEE Industrial Submetering Guide: 6-10% energy reduction through behavioral and peak control.",
            derivation_type="benchmark-based",
            justification="Provides visibility into unmonitored circuits to enable systematic load trimming."
        )
        db.add(r)
        recommendations.append(r)

    db.commit()
    return recommendations
