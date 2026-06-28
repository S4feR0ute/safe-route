from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("street_segments.id", ondelete="CASCADE"), index=True)
    district_score = Column(Float, default=0.5)
    context_score  = Column(Float, default=0.5)
    report_score   = Column(Float, default=0.0)
    composite_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
