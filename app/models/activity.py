from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # energy, material, waste, process
    item_name = Column(String(100), nullable=False)
    factor_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source_name = Column(String(150), nullable=False)
    source_reference = Column(String(255), nullable=True)
    region = Column(String(100), default="India")
    version_year = Column(String(20), default="2024")

class EnergySource(Base):
    __tablename__ = "energy_sources"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)
    annual_consumption = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="kWh/year")
    emission_factor = Column(Float, nullable=False, default=0.48)
    factor_source = Column(String(150), nullable=True, default="Configured Grid Factor")
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="energy_sources")

class MaterialInput(Base):
    __tablename__ = "material_inputs"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    material_type = Column(String(100), nullable=False)
    annual_quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="kg/year")
    recycled_content_percent = Column(Float, nullable=False, default=0.0)
    emission_factor = Column(Float, nullable=False, default=8.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="material_inputs")

class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    equipment = Column(String(150), nullable=True)
    operating_hours = Column(Float, nullable=False, default=0.0)
    primary_energy_source = Column(String(100), nullable=True, default="Grid Electricity")
    operating_pressure_bar = Column(Float, nullable=True, default=0.0)
    estimated_leakage_percent = Column(Float, nullable=True, default=0.0)
    annual_energy_kwh = Column(Float, nullable=True, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="processes")

class WasteStream(Base):
    __tablename__ = "waste_streams"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    waste_type = Column(String(100), nullable=False)
    annual_quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="kg/year")
    treatment_method = Column(String(100), nullable=False, default="Landfill / Disposal")
    emission_factor = Column(Float, nullable=False, default=2.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="waste_streams")
