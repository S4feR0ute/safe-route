from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    user_type = Column(String(20), default="citizen", index=True, nullable=False)
    moderator_since = Column(DateTime, nullable=True)   # Cuándo se convirtió en moderador
    is_verified_moderator = Column(Boolean, default=False, index=True)
    moderator_role = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete

    # Un usuario puede tener muchos reportes
    reports = relationship(
        "IncidentReport",
        back_populates="user",
        foreign_keys="IncidentReport.user_id",
        lazy="select"
    )
