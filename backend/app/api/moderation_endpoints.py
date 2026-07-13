import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.auth_helper import get_moderator
from app.core.exceptions import ValidationError
from app.core.service_container import ServiceContainer, get_service_container
from app.schemas.report_schemas import (
    ReportResponse,
    ReportValidateRequest,
    ReportListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/moderation", tags=["moderation"])


@router.get("/queue", response_model=ReportListResponse)
async def get_moderation_queue(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    incident_type: Optional[str] = None,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """Obtiene cola de reportes pendientes de moderación."""
    reports, total = container.get_moderation_service().get_pending_reports(
        limit=limit,
        offset=offset,
        incident_type=incident_type,
    )
    return ReportListResponse(
        total=total,
        reports=[ReportResponse.model_validate(r) for r in reports],
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_detail(
    report_id: str,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """Obtiene detalles de un reporte específico para moderación."""
    report = container.get_moderation_service().get_report_detail(report_id)
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/approve", response_model=ReportResponse)
async def approve_report(
    report_id: str,
    request: ReportValidateRequest,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """Aprueba un reporte (status: pending -> validated)."""
    if request.status != "validated":
        raise ValidationError(
            "Status debe ser 'validated' para aprobar un reporte",
            details={"field": "status"},
        )

    report = container.get_moderation_service().approve_report(
        report_id=report_id,
        moderator=moderator,
        validation_notes=request.reason,
    )
    logger.info(f"Reporte {report_id} aprobado por moderador {moderator.id} ({moderator.email})")
    return ReportResponse.model_validate(report)


@router.patch("/{report_id}/reject", response_model=ReportResponse)
async def reject_report(
    report_id: str,
    request: ReportValidateRequest,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Rechaza un reporte (status: pending -> rejected).
    Requiere reason (motivo del rechazo).
    """
    if request.status != "rejected":
        raise ValidationError(
            "Status debe ser 'rejected' para rechazar un reporte",
            details={"field": "status"},
        )

    report = container.get_moderation_service().reject_report(
        report_id=report_id,
        moderator=moderator,
        validation_notes=request.reason,
    )
    logger.info(
        f"Reporte {report_id} rechazado por moderador {moderator.id} ({moderator.email}). "
        f"Motivo: {request.reason}"
    )
    return ReportResponse.model_validate(report)


@router.get("/stats/dashboard")
async def get_moderation_stats(
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """Obtiene estadísticas de moderación para el dashboard."""
    stats = container.get_moderation_service().get_moderation_stats()
    return {"status": "ok", "data": stats}
