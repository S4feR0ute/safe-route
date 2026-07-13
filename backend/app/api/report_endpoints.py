from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, status, Form, Query

from app.schemas.report_schemas import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    ReportResponse,
    ReportMapResponse,
    ReportMapListResponse,
)
from app.core.constants import INCIDENT_TYPES
from app.core.exceptions import ValidationError
from app.core.service_container import ServiceContainer, get_service_container
from app.core.auth_helper import get_current_user_optional, get_current_user

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReportResponse)
async def create_report(
    incident_type: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: Optional[str] = Form(None),
    incident_date: Optional[str] = Form(
        None,
        description="Fecha del incidente en formato ISO (modo 2/3, requiere cuenta)",
    ),
    file: Optional[UploadFile] = File(None),
    container: ServiceContainer = Depends(get_service_container),
    current_user = Depends(get_current_user_optional),
):
    """
    Crea un reporte (multipart/form-data). El modo se deduce:
    1 = anónimo · 2 = con cuenta (+fecha del incidente) · 3 = con cuenta + archivo.
    """
    occurred_at = None
    if incident_date:
        try:
            occurred_at = datetime.fromisoformat(incident_date)
        except ValueError:
            raise ValidationError(
                "incident_date debe ser una fecha ISO válida (ej: 2026-07-01 o 2026-07-01T21:30:00)",
                details={"field": "incident_date"},
            )

    report = await container.get_report_service().create_report(
        incident_type=incident_type,
        latitude=latitude,
        longitude=longitude,
        description=description,
        user_id=current_user.id if current_user else None,
        occurred_at=occurred_at,
        file=file,
    )
    return ReportResponse.model_validate(report)


@router.get("", response_model=ReportMapListResponse)
async def list_public_reports(
    incident_type: Optional[str] = Query(None),
    bbox: Optional[str] = Query(
        None,
        description="Filtro geográfico: min_lon,min_lat,max_lon,max_lat",
    ),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Lista reportes validados para el mapa público (RF-19).
    Solo expone campos no sensibles (nunca identidad del reportante).
    """
    if incident_type and incident_type not in INCIDENT_TYPES:
        raise ValidationError(
            f"incident_type inválido. Válidos: {', '.join(sorted(INCIDENT_TYPES))}",
            details={"field": "incident_type"},
        )

    parsed_bbox = _parse_bbox(bbox) if bbox else None

    reports, total = container.get_report_service().get_public_reports(
        incident_type=incident_type,
        bbox=parsed_bbox,
        limit=limit,
        offset=offset,
    )
    return ReportMapListResponse(
        total=total,
        reports=[ReportMapResponse.model_validate(r) for r in reports],
    )


def _parse_bbox(bbox: str) -> tuple:
    """Parsea 'min_lon,min_lat,max_lon,max_lat' validando mínimos < máximos."""
    try:
        parts = [float(p) for p in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError
        min_lon, min_lat, max_lon, max_lat = parts
        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError
        return (min_lon, min_lat, max_lon, max_lat)
    except ValueError:
        raise ValidationError(
            "bbox debe ser 'min_lon,min_lat,max_lon,max_lat' con mínimos < máximos",
            details={"field": "bbox"},
        )


@router.post("/{report_id}/documents", response_model=DocumentUploadResponse)
async def upload_report_document(
    report_id: str,
    file: UploadFile = File(...),
    container: ServiceContainer = Depends(get_service_container),
    current_user = Depends(get_current_user),
):
    """Adjunta un documento a un reporte propio (lo promueve a modo 3)."""
    document = await container.get_report_service().add_document(
        report_id, file, user=current_user
    )
    return DocumentUploadResponse(
        document_id=document.id,
        report_id=document.report_id,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        original_filename=document.original_filename,
        file_path=document.file_path,
        uploaded_at=document.uploaded_at,
    )


@router.get("/{report_id}/documents", response_model=DocumentListResponse)
async def get_report_documents(
    report_id: str,
    container: ServiceContainer = Depends(get_service_container),
    current_user = Depends(get_current_user),
):
    """Lista los documentos de un reporte (autor o moderador)."""
    documents, total_size = container.get_report_service().get_documents(
        report_id, user=current_user
    )
    return DocumentListResponse(
        report_id=report_id,
        total_documents=len(documents),
        total_size_bytes=total_size,
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
    )


@router.delete("/{report_id}/documents/{document_id}")
async def delete_report_document(
    report_id: str,
    document_id: str,
    container: ServiceContainer = Depends(get_service_container),
    current_user = Depends(get_current_user),
):
    """Elimina un documento de un reporte (autor o moderador)."""
    container.get_report_service().remove_document(
        report_id, document_id, user=current_user
    )
    return {"message": "Documento eliminado correctamente"}
