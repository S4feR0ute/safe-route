import logging
from fastapi import APIRouter, Depends, status
from typing import Optional

from app.core.auth_helper import get_moderator
from app.core.error_handler import ErrorHandler
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
    limit: int = 50,
    offset: int = 0,
    incident_type: Optional[str] = None,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Obtiene cola de reportes pendientes de moderación.
    """
    try:
        service = container.get_moderation_service()

        # Validar parámetros
        limit = min(limit, 500)
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0

        reports, total = service.get_pending_reports(
            limit=limit,
            offset=offset,
            incident_type=incident_type
        )

        return ReportListResponse(
            total=total,
            reports=[ReportResponse.model_validate(r) for r in reports]
        )

    except Exception as e:
        logger.exception(f"Moderation queue error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al obtener cola de moderación"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_detail(
    report_id: str,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Obtiene detalles de un reporte específico para moderación.
    """
    try:
        service = container.get_moderation_service()
        report = service.get_report_detail(report_id)
        return ReportResponse.model_validate(report)

    except ValueError as e:
        return ErrorHandler.not_found(str(e))
    except Exception as e:
        logger.exception(f"Get report detail error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al obtener detalles del reporte"
        )


@router.patch("/{report_id}/approve", response_model=ReportResponse)
async def approve_report(
    report_id: str,
    request: ReportValidateRequest,
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Aprueba un reporte (status: pending -> validated).
    """
    try:
        if request.status != "validated":
            return ErrorHandler.validation_error(
                message="Status debe ser 'validated' para aprobar un reporte",
                field="status"
            )

        service = container.get_moderation_service()
        report = service.approve_report(
            report_id=report_id,
            moderator=moderator,
            validation_notes=request.reason
        )

        logger.info(
            f"Reporte {report_id} aprobado por moderador {moderator.id} ({moderator.email})"
        )

        return ReportResponse.model_validate(report)

    except ValueError as e:
        container.db.rollback()
        return ErrorHandler.not_found(str(e))
    except Exception as e:
        logger.exception(f"Approve report error: {type(e).__name__}")
        container.db.rollback()
        return ErrorHandler.internal_error(
            message="Error al aprobar reporte"
        )


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
    try:
        if request.status != "rejected":
            return ErrorHandler.validation_error(
                message="Status debe ser 'rejected' para rechazar un reporte",
                field="status"
            )

        if not request.reason or request.reason.strip() == "":
            return ErrorHandler.validation_error(
                message="Debe proporcionar un motivo para rechazar el reporte",
                field="reason"
            )

        service = container.get_moderation_service()
        report = service.reject_report(
            report_id=report_id,
            moderator=moderator,
            validation_notes=request.reason
        )

        logger.info(
            f"Reporte {report_id} rechazado por moderador {moderator.id} ({moderator.email}). "
            f"Motivo: {request.reason}"
        )

        return ReportResponse.model_validate(report)

    except ValueError as e:
        container.db.rollback()
        if "no encontrado" in str(e):
            return ErrorHandler.not_found(str(e))
        return ErrorHandler.validation_error(message=str(e), field="report_id")
    except Exception as e:
        logger.exception(f"Reject report error: {type(e).__name__}")
        container.db.rollback()
        return ErrorHandler.internal_error(
            message="Error al rechazar reporte"
        )


@router.get("/stats/dashboard")
async def get_moderation_stats(
    moderator=Depends(get_moderator),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Obtiene estadísticas de moderación para el dashboard.
    """
    try:
        service = container.get_moderation_service()
        stats = service.get_moderation_stats()
        return {
            "status": "ok",
            "data": stats
        }

    except Exception as e:
        logger.exception(f"Moderation stats error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al obtener estadísticas de moderación"
        )
