from typing import Optional, List
from pydantic import BaseModel

class EnergySourceIn(BaseModel):
    source_type: str
    annual_consumption: float
    unit: str = "kWh/year"
    emission_factor: float = 0.48
    factor_source: Optional[str] = "Configured Grid Factor"

class MaterialInputIn(BaseModel):
    material_type: str
    annual_quantity: float
    unit: str = "kg/year"
    recycled_content_percent: float = 0.0
    emission_factor: float = 8.0

class ProcessIn(BaseModel):
    name: str
    equipment: Optional[str] = None
    operating_hours: float = 0.0
    primary_energy_source: Optional[str] = "Grid Electricity"
    operating_pressure_bar: Optional[float] = 0.0
    estimated_leakage_percent: Optional[float] = 0.0
    annual_energy_kwh: Optional[float] = 0.0
    notes: Optional[str] = None

class WasteStreamIn(BaseModel):
    waste_type: str
    annual_quantity: float
    unit: str = "kg/year"
    treatment_method: str = "Landfill / Disposal"
    emission_factor: float = 2.0

class ActivityDataPayload(BaseModel):
    energy_sources: List[EnergySourceIn] = []
    material_inputs: List[MaterialInputIn] = []
    processes: List[ProcessIn] = []
    waste_streams: List[WasteStreamIn] = []

class ActivityDataResponse(BaseModel):
    energy_sources: List[dict]
    material_inputs: List[dict]
    processes: List[dict]
    waste_streams: List[dict]
