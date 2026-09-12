from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), nullable=True)
    code = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    target_process = Column(String(100), nullable=False)
    root_cause = Column(String(150), nullable=False)
    carbon_saving_tco2e = Column(Float, nullable=False, default=0.0)
    reduction_pct = Column(Float, nullable=False, default=0.0)
    estimated_cost_inr_lakhs = Column(Float, nullable=False, default=0.0)
    payback_months = Column(Float, nullable=False, default=0.0)
    effort_level = Column(String(50), nullable=False, default="Low")  # Low, Medium, High
    confidence_pct = Column(Float, nullable=False, default=85.0)
    disruption_level = Column(String(50), nullable=False, default="Low")
    assumption_reference = Column(Text, nullable=True)
    derivation_type = Column(String(50), default="calculated")  # measured, calculated, benchmark-based, assumed
    justification = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="recommendations")
    hotspot = relationship("Hotspot", back_populates="recommendations")
    scenarios = relationship("Scenario", back_populates="recommendation")
