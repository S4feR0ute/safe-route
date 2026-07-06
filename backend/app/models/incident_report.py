from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from uuid import uuid4
from app.db.base import Base


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_type = Column(String(100), index=True, nullable=False)
    location = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(String(1000), nullable=True)
    occurred_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", index=True)
    mode = Column(Integer, default=1, index=True)  # 1=anón, 2=auth, 3=auth+docs
    severity_level = Column(String(20), default="medium")
    has_documents = Column(Boolean, default=False, index=True)
    document_count = Column(Integer, default=0)
    evidence_quality_score = Column(Float, default=0.0)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(String(1000), nullable=True)
    validated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ORM
    user = relationship(
        "User",
        back_populates="reports",
        foreign_keys=[user_id],
        lazy="select"
    )
    documents = relationship(
        "ReportDocument",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
        Index("idx_type_created", "incident_type", "created_at"),
    )
