from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ScenarioPreviewRequest(BaseModel):
    recommendation_id: Optional[int] = None
    recommendation_code: Optional[str] = None
    implementation_percent: float = 100.0
    performance_percent: float = 100.0
    cost_variation_percent: float = 100.0

class ScenarioPreviewResponse(BaseModel):
    baseline_tco2e: float
    recommendation_title: str
    implementation_percent: float
    performance_percent: float
    cost_variation_percent: float
    effective_saving_tco2e: float
    future_footprint_tco2e: float
    reduction_percent: float
    estimated_cost_inr_lakhs: float
    confidence_pct: float

class ScenarioSaveRequest(ScenarioPreviewRequest):
    title: Optional[str] = None

class ScenarioResponse(ScenarioPreviewResponse):
    id: int
    factory_id: int
    title: Optional[str] = None
    created_at: datetime
