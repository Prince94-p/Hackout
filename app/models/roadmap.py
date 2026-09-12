from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    baseline_tco2e = Column(Float, nullable=False, default=0.0)
    planned_saving_tco2e = Column(Float, nullable=False, default=0.0)
    target_footprint_tco2e = Column(Float, nullable=False, default=0.0)
    reduction_percent = Column(Float, nullable=False, default=0.0)
    total_cost_inr_lakhs = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="roadmaps")
    actions = relationship("RoadmapAction", back_populates="roadmap", cascade="all, delete-orphan")

class RoadmapAction(Base):
    __tablename__ = "roadmap_actions"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    order_index = Column(Integer, nullable=False, default=1)
    action_title = Column(String(200), nullable=False)
    phase_label = Column(String(100), nullable=False, default="Phase 1: Quick Wins")
    carbon_saving_tco2e = Column(Float, nullable=False, default=0.0)
    cost_inr_lakhs = Column(Float, nullable=False, default=0.0)
    effort_level = Column(String(50), nullable=False, default="Low")
    confidence_pct = Column(Float, nullable=False, default=85.0)
    status = Column(String(50), nullable=False, default="Planned")

    roadmap = relationship("Roadmap", back_populates="actions")
