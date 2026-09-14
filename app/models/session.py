from sqlalchemy import Column, String, DateTime
from app.database import Base

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    token_hash = Column(String(64), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
