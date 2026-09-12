from typing import List, Optional
from pydantic import BaseModel

class RoadmapActionResponse(BaseModel):
    id: int
    order_index: int
    action_title: str
    phase_label: str
    carbon_saving_tco2e: float
    cost_inr_lakhs: float
    effort_level: str
    confidence_pct: float
    status: str

class RoadmapResponse(BaseModel):
    id: Optional[int] = None
    factory_id: int
    baseline_tco2e: float
    planned_saving_tco2e: float
    target_footprint_tco2e: float
    reduction_percent: float
    total_cost_inr_lakhs: float
    timeline_steps: List[dict]
    actions: List[RoadmapActionResponse]
