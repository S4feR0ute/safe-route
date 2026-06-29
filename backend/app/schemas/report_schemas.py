from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.core.validators import InputValidator


class LocationInput(BaseModel):
    """Ubicación para un reporte."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Coordenadas deben ser números")
        return float(v)


class ReportCreateRequest(BaseModel):
    """Request para crear reporte (modo 1 o 2)."""
    incident_type: str = Field(..., min_length=1, max_length=100)
    location: LocationInput
    description: Optional[str] = Field(None, max_length=1000)
    # mode se deduce: 1 si anon, 2 si auth

    @field_validator("incident_type", mode="before")
    @classmethod
    def validate_incident_type(cls, v: str) -> str:
        return InputValidator.validate_string(v, "incident_type", max_length=100)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return InputValidator.validate_string(v, "description", max_length=1000)


class ReportResponse(BaseModel):
    """Response de un reporte."""
    id: str
    incident_type: str
    latitude: float
    longitude: float
    description: Optional[str]
    status: str  # pending, validated, rejected
    mode: int  # 1, 2, 3
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    validated_at: Optional[datetime]
    validated_by_user_id: Optional[int]

    model_config = {
        "from_attributes": True
    }


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


class ReportValidateResponse(BaseModel):
    """Response de validación."""
    success: bool
    report: ReportResponse
    validated_by_user_id: int
    validated_at: datetime


class ReportMapResponse(BaseModel):
    """Response de reportes para visualizar en mapa."""
    id: str
    incident_type: str
    latitude: float
    longitude: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response exitoso de carga de documento."""
    document_id: str
    report_id: str
    file_type: str
    file_size_bytes: int
    original_filename: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Response de un documento."""
    id: str
    report_id: str
    file_type: str
    file_size_bytes: int
    original_filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response de lista de documentos de un reporte."""
    report_id: str
    total_documents: int
    total_size_bytes: int
    documents: List[DocumentResponse]


class DocumentUploadErrorResponse(BaseModel):
    """Response de error en carga de documento."""
    error: dict = Field(..., description="Error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "FILE_SIZE_EXCEEDED",
                    "message": "Archivo supera límite de 10MB",
                    "details": {}
                }
            }
        }
    }


class IncidentTypeListResponse(BaseModel):
    """Lista de tipos de incidencia disponibles."""
    types: List[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "types": [
                    "robo",
                    "asalto",
                    "violencia",
                    "droga",
                    "otro"
                ]
            }
        }
    }
