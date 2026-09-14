import json
from typing import Dict, Any
from app.models.factory import Factory
from app.models.hotspot import Hotspot


def diagnose_root_cause(factory: Factory, hotspot: Hotspot) -> Dict[str, Any]:
    """Separate submitted observations from hypotheses requiring an onsite audit."""
    details = json.loads(hotspot.details_json or '{}')
    carbon = hotspot.carbon_tco2e
    activity = details.get('activity_basis', details.get('energy_str', 'Not available'))
    factor = details.get('factor_str', 'Not available')
    evidence = [f'Entered activity: {activity}.', f'Configured factor: {factor}.', f'Calculated footprint: {carbon} tCO₂e/year.']
    wasted = 'Avoidable loss is not quantified'
    condition = hotspot.operating_condition or 'Not reported'
    target = 'Verify operating requirements'
    reason = 'The entered activity and factor explain this footprint. Metering and an onsite assessment are needed to establish avoidable losses.'
    process = next((p for p in factory.processes if p.name == hotspot.title), None) if hotspot.category == 'Energy' else None
    if process and ('air' in process.name.lower() or 'compress' in process.name.lower()):
        leakage = process.estimated_leakage_percent or 0
        wasted_kwh = (process.annual_energy_kwh or 0) * leakage / 100
        wasted = f'{wasted_kwh:,.2f} kWh/year estimated leakage loss'
        evidence.append(f'User-entered leakage estimate: {leakage}%; implied energy loss: {wasted_kwh:,.2f} kWh/year.')
        reason = 'Inspect and measure the reported leakage. Pressure reduction requires confirmation of the equipment minimum pressure; excessive pressure is not established by this form alone.'
    elif hotspot.category == 'Materials':
        target = 'Obtain supplier-specific recycled factor'
        reason = 'The entered material factor explains embodied emissions. A recycled alternative is beneficial only if its verified factor is lower and product requirements are met.'
    elif hotspot.category == 'Waste':
        target = 'Verify treatment and recovery alternatives'
        reason = 'The entered quantity and treatment factor explain waste emissions. Assess compatible recovery routes before claiming avoided disposal emissions.'
    return {
        'hotspot_code': hotspot.code, 'summary_carbon': carbon,
        'summary_unit': f'tCO₂e · {hotspot.title}', 'process_name': hotspot.title,
        'carbon_str': f'{carbon} tCO₂e / year', 'signal_str': hotspot.signal_value,
        'condition_str': condition, 'root_cause_label': f'{hotspot.title}: activity and emission factor',
        'root_cause_text': reason, 'root_cause_title': f'Investigate {hotspot.title}',
        'root_cause_description': reason, 'leakage_metric': hotspot.signal_value,
        'wasted_metric': wasted, 'pressure_metric': condition, 'target_metric': target,
        'diagnostic_reason': reason, 'evidence_points': evidence,
        'assumptions': ['User-entered activity and factors require independent verification.'],
        'confidence_pct': hotspot.confidence_pct, 'factor_str': factor,
        'equation_activity': activity, 'equation_carbon': f'{carbon} tCO₂e'
    }
