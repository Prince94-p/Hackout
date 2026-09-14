from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator

class InputModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, str_strip_whitespace=True)

class EnergySourceIn(InputModel):
    source_type: str = Field(..., min_length=1)
    annual_consumption: float = Field(..., ge=0)
    unit: str = "kWh/year"
    emission_factor: float = Field(..., ge=0)
    factor_source: Optional[str] = "Configured Grid Factor"

class MaterialInputIn(InputModel):
    material_type: str = Field(..., min_length=1)
    annual_quantity: float = Field(..., ge=0)
    unit: str = "kg/year"
    recycled_content_percent: float = Field(0.0, ge=0, le=100)
    emission_factor: float = Field(..., ge=0)

class ProcessIn(InputModel):
    name: str = Field(..., min_length=1)
    equipment: Optional[str] = None
    operating_hours: float = Field(0.0, ge=0)
    primary_energy_source: Optional[str] = "Grid Electricity"
    operating_pressure_bar: float = Field(0.0, ge=0)
    estimated_leakage_percent: float = Field(0.0, ge=0, le=100)
    annual_energy_kwh: float = Field(0.0, ge=0)
    notes: Optional[str] = None

class WasteStreamIn(InputModel):
    waste_type: str = Field(..., min_length=1)
    annual_quantity: float = Field(..., ge=0)
    unit: str = "kg/year"
    treatment_method: str = "Landfill / Disposal"
    emission_factor: float = Field(..., ge=0)

class ActivityDataPayload(InputModel):
    energy_sources: List[EnergySourceIn] = []
    material_inputs: List[MaterialInputIn] = []
    processes: List[ProcessIn] = []
    waste_streams: List[WasteStreamIn] = []

    @model_validator(mode="after")
    def consistent_activity(self):
        quantities = [e.annual_consumption for e in self.energy_sources] + [m.annual_quantity for m in self.material_inputs] + [w.annual_quantity for w in self.waste_streams]
        if not any(q > 0 for q in quantities):
            raise ValueError("Enter at least one positive activity quantity before calculating")
        allocated = {}
        for process in self.processes:
            source = process.primary_energy_source
            allocated[source] = allocated.get(source, 0) + process.annual_energy_kwh
        for source, amount in allocated.items():
            available = sum(e.annual_consumption for e in self.energy_sources if e.source_type == source)
            if amount > available + 0.000001:
                raise ValueError(f"Process energy allocated to {source} exceeds its entered consumption")
        return self

class ActivityDataResponse(InputModel):
    energy_sources: List[dict]
    material_inputs: List[dict]
    processes: List[dict]
    waste_streams: List[dict]
