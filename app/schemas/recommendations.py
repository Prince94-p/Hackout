from typing import Optional
from pydantic import BaseModel

class RecommendationResponse(BaseModel):
    id: int
    code: str
    title: str
    description: str
    category: str
    target_process: str
    root_cause: str
    carbon_saving_tco2e: float
    reduction_pct: float
    estimated_cost_inr_lakhs: float
    payback_months: float
    effort_level: str
    confidence_pct: float
    disruption_level: str
    assumption_reference: Optional[str] = None
    derivation_type: str
    justification: Optional[str] = None
