from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    title = Column(String(200), nullable=False)
    implementation_percent = Column(Float, nullable=False, default=100.0)
    performance_percent = Column(Float, nullable=False, default=100.0)
    cost_variation_percent = Column(Float, nullable=False, default=100.0)
    effective_saving_tco2e = Column(Float, nullable=False, default=0.0)
    future_footprint_tco2e = Column(Float, nullable=False, default=0.0)
    reduction_percent = Column(Float, nullable=False, default=0.0)
    estimated_cost_inr_lakhs = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="scenarios")
    recommendation = relationship("Recommendation", back_populates="scenarios")
