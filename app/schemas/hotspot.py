from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class HotspotResponse(BaseModel):
    id: int
    rank: int
    code: str
    title: str
    category: str
    branch_path: str
    carbon_tco2e: float
    share_pct: float
    signal_type: str
    signal_value: str
    operating_condition: Optional[str] = None
    confidence_pct: float
    details: Optional[Dict[str, Any]] = None

class RootCauseResponse(BaseModel):
    hotspot_code: str
    summary_carbon: float
    summary_unit: str
    process_name: str
    carbon_str: str
    signal_str: str
    condition_str: str
    root_cause_label: str
    root_cause_text: str
    root_cause_title: str
    root_cause_description: str
    leakage_metric: str
    wasted_metric: str
    pressure_metric: str
    target_metric: str
    diagnostic_reason: str
    evidence_points: List[str]
    assumptions: List[str]
    confidence_pct: float
