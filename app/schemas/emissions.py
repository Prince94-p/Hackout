from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel

class ConfidenceBreakdown(BaseModel):
    activity_data_completeness: float
    factor_quality: float
    operational_signal_completeness: float
    evidence_quality: float

class FactorTraceabilityItem(BaseModel):
    category: str
    item_name: str
    factor_value: float
    unit: str
    source_name: str
    source_reference: Optional[str] = None
    region: str = "India"
    version_year: str = "2024"

class EmissionCalculateResponse(BaseModel):
    total_tco2e: float
    energy_tco2e: float
    material_tco2e: float
    waste_tco2e: float
    energy_pct: float
    material_pct: float
    waste_pct: float
    largest_source: str
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    factor_traceability: List[FactorTraceabilityItem]
    calculation_date: datetime

class EmissionSummaryResponse(BaseModel):
    has_calculation: bool
    factory_name: str
    baseline: float
    total_carbon_tco2e: Optional[float] = None
    energy_tco2e: float
    material_tco2e: float
    waste_tco2e: float
    energy_pct: float
    material_pct: float
    waste_pct: float
    largest_source: str
    top_share_pct: float
    priority_leak: Optional[str] = None
    priority_leak_pct: Optional[str] = None
    wasted_kwh: Optional[float] = None
    priority_footprint: Optional[float] = None
    operating_pressure: Optional[str] = None
    confidence: float
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    source_distribution: List[Dict[str, Any]] = []
    investigation_queue: List[Dict[str, Any]] = []
