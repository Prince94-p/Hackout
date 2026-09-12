from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False, default=1)
    code = Column(String(50), nullable=False, default="compressed-air")
    title = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # Energy, Materials, Waste, Process
    branch_path = Column(String(150), nullable=False)  # e.g. "Energy → Utilities → Compressed Air"
    carbon_tco2e = Column(Float, nullable=False, default=0.0)
    share_pct = Column(Float, nullable=False, default=0.0)
    signal_type = Column(String(100), nullable=False)
    signal_value = Column(String(100), nullable=False)
    operating_condition = Column(String(150), nullable=True)
    confidence_pct = Column(Float, nullable=False, default=85.0)
    details_json = Column(Text, nullable=True)  # JSON details: reason, description, intervention
    created_at = Column(DateTime, default=datetime.utcnow)

    factory = relationship("Factory", back_populates="hotspots")
    recommendations = relationship("Recommendation", back_populates="hotspot")
