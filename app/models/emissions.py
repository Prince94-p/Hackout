from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class EmissionRecord(Base):
    __tablename__ = "emission_records"

    id = Column(Integer, primary_key=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=False, index=True)
    calculation_date = Column(DateTime, default=datetime.utcnow)
    total_tco2e = Column(Float, nullable=False, default=0.0)
    energy_tco2e = Column(Float, nullable=False, default=0.0)
    material_tco2e = Column(Float, nullable=False, default=0.0)
    waste_tco2e = Column(Float, nullable=False, default=0.0)
    energy_pct = Column(Float, nullable=False, default=0.0)
    material_pct = Column(Float, nullable=False, default=0.0)
    waste_pct = Column(Float, nullable=False, default=0.0)
    largest_source = Column(String(50), nullable=False, default="Energy")
    confidence_score = Column(Float, nullable=False, default=80.0)
    confidence_breakdown = Column(Text, nullable=True)  # JSON-encoded dictionary
    factor_traceability = Column(Text, nullable=True)   # JSON-encoded list of factor citations
    details_json = Column(Text, nullable=True)          # JSON-encoded process and stream calculations

    factory = relationship("Factory", back_populates="emission_records")
