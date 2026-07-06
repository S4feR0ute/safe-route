from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.core.validators import InputValidator


class ReportResponse(BaseModel):
    """Response de un reporte."""
    id: str
    incident_type: str
    latitude: float
    longitude: float
    description: Optional[str]
    occurred_at: Optional[datetime]
    status: str  # pending, validated, rejected
    mode: int  # 1=anónimo, 2=autenticado, 3=autenticado+documentos
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    validated_at: Optional[datetime]
    validated_by_user_id: Optional[int]

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Response de lista de reportes."""
    total: int
    reports: List[ReportResponse]


class ReportValidateRequest(BaseModel):
    """Request para validar reporte (moderador)."""
    status: str = Field(..., pattern="^(validated|rejected)$")
    reason: Optional[str] = Field(None, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def validate_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return InputValidator.validate_string(v, "reason", max_length=500)


class ReportMapResponse(BaseModel):
    """Reporte público para visualizar en el mapa."""
    id: str
    incident_type: str
    latitude: float
    longitude: float
    severity_level: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportMapListResponse(BaseModel):
    """Lista de reportes públicos para el mapa (RF-19)."""
    total: int
    reports: List[ReportMapResponse]


class DocumentUploadResponse(BaseModel):
    """Response exitoso de carga de documento."""
    document_id: str
    report_id: str
    file_type: str
    file_size_bytes: int
    original_filename: str
    file_path: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    """Response de un documento."""
    id: str
    report_id: str
    file_type: str
    file_size_bytes: int
    original_filename: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Response de lista de documentos de un reporte."""
    report_id: str
    total_documents: int
    total_size_bytes: int
    documents: List[DocumentResponse]
