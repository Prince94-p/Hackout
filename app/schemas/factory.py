from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class FactoryCreate(BaseModel):
    name: str
    industry: str
    location: str
    reporting_period: str
    annual_production: float
    production_unit: str
    selected_processes: Optional[List[str]] = None

class FactoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    industry: str
    location: str
    reporting_period: str
    annual_production: float
    production_unit: str
    selected_processes: Optional[str] = None
    is_demo: bool
    created_at: datetime

    model_config = {"from_attributes": True}
