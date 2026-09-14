from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ScenarioPreviewRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    recommendation_id: Optional[int] = None
    recommendation_code: Optional[str] = None
    implementation_percent: float = Field(100.0, ge=0, le=100)
    performance_percent: float = Field(100.0, ge=0, le=110)
    cost_variation_percent: float = Field(0.0, ge=-100, le=100)

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
    title: Optional[str] = Field(None, max_length=200)

class ScenarioResponse(ScenarioPreviewResponse):
    id: int
    factory_id: int
    title: Optional[str] = Field(None, max_length=200)
    created_at: datetime
