from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

class FactoryCreate(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    reporting_period: str = Field(..., min_length=1)
    annual_production: float = Field(..., ge=0)
    production_unit: str = Field(..., min_length=1)
    selected_processes: Optional[List[str]] = None

    @field_validator('name', 'industry', 'location', 'reporting_period', 'production_unit')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

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
