from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.incident_report import IncidentReport
from app.models.user import User
from app.interfaces.incident_report_interface import IIncidentReportRepository
from app.repositories.factory import RepositoryFactory
from app.core.exceptions import ReportNotFoundError, InvalidReportStateError
from app.db.transactions import transaction_no_close


class ModerationService:
    """
    Servicio de moderación de reportes ciudadanos.
    Cada método público es la frontera transaccional: commit al salir sin error, rollback en excepción.
    """

    def __init__(self, db: Session, incident_repo: IIncidentReportRepository = None):
        self.db = db
        self.incident_repo = incident_repo or RepositoryFactory.create_incident_repository(db)

    def get_pending_reports(
        self,
        limit: int = 50,
        offset: int = 0,
        incident_type: Optional[str] = None
    ) -> Tuple[List[IncidentReport], int]:
        """Obtiene reportes pendientes de moderación, paginados."""
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        return self.incident_repo.get_pending_paginated(
            limit=limit, offset=offset, incident_type=incident_type
        )

    def approve_report(
        self,
        report_id: str,
        moderator: User,
        validation_notes: Optional[str] = None
    ) -> IncidentReport:
        """Aprueba un reporte (status: pending -> validated)."""
        report = self._get_pending_report(report_id)

        with transaction_no_close(self.db):
            report.status = "validated"
            report.validated_at = datetime.utcnow()
            report.validated_by_user_id = moderator.id
            report.validation_notes = validation_notes

        return report

    def reject_report(
        self,
        report_id: str,
        moderator: User,
        validation_notes: Optional[str] = None
    ) -> IncidentReport:
        """Rechaza un reporte (status: pending -> rejected)."""
        report = self._get_pending_report(report_id)

        if not validation_notes or validation_notes.strip() == "":
            raise ValueError("Debe proporcionar un motivo para rechazar el reporte")

        with transaction_no_close(self.db):
            report.status = "rejected"
            report.validated_at = datetime.utcnow()
            report.validated_by_user_id = moderator.id
            report.validation_notes = validation_notes

        return report

    def get_moderation_stats(self) -> dict:
        """Obtiene estadísticas de moderación (conteo por estado)."""
        return self.incident_repo.count_by_status()

    def get_report_detail(self, report_id: str) -> IncidentReport:
        """Obtiene detalles completos de un reporte para moderación."""
        report = self.incident_repo.get_by_id(report_id)
        if not report:
            raise ReportNotFoundError(f"Reporte {report_id} no encontrado")
        return report

    def _get_pending_report(self, report_id: str) -> IncidentReport:
        """Busca el reporte y valida que esté pendiente."""
        report = self.incident_repo.get_by_id(report_id)

        if not report:
            raise ReportNotFoundError(f"Reporte {report_id} no encontrado")

        if report.status != "pending":
            raise InvalidReportStateError(
                f"Reporte no está pendiente (estado actual: {report.status})"
            )

        return report
