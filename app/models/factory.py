from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Factory(Base):
    __tablename__ = "factories"

    id = Column(Integer, primary_key=True, index=True)
    request_key = Column(String(64), nullable=True, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    reporting_period = Column(String(100), nullable=False)
    annual_production = Column(Float, nullable=False, default=0.0)
    production_unit = Column(String(50), nullable=False, default="units")
    selected_processes = Column(Text, nullable=True)  # JSON-encoded array of process names
    is_demo = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="factories")
    energy_sources = relationship("EnergySource", back_populates="factory", cascade="all, delete-orphan")
    material_inputs = relationship("MaterialInput", back_populates="factory", cascade="all, delete-orphan")
    processes = relationship("Process", back_populates="factory", cascade="all, delete-orphan")
    waste_streams = relationship("WasteStream", back_populates="factory", cascade="all, delete-orphan")
    emission_records = relationship("EmissionRecord", back_populates="factory", cascade="all, delete-orphan")
    hotspots = relationship("Hotspot", back_populates="factory", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="factory", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="factory", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="factory", cascade="all, delete-orphan")
