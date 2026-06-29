from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db.base import Base


class ReportDocument(Base):
    __tablename__ = "report_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    report_id = Column(String(36), ForeignKey("incident_reports.id", ondelete="CASCADE"), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash_sha256 = Column(String(64), unique=True, index=True, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_type = Column(String(50), default="local")
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    original_filename = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)

    # Relación ORM
    report = relationship(
        "IncidentReport",
        back_populates="documents",
        lazy="select"
    )

    __table_args__ = (Index("idx_report_uploaded", "report_id", "uploaded_at"),)
