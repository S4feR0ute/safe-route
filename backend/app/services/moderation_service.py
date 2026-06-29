from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.incident_report import IncidentReport
from app.models.user import User
from app.repositories.factory import RepositoryFactory


class ModerationService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = RepositoryFactory.create_incident_repository(db)

    def get_pending_reports(
        self,
        limit: int = 50,
        offset: int = 0,
        incident_type: Optional[str] = None
    ) -> Tuple[List[IncidentReport], int]:
        """
        Obtiene reportes pendientes de moderación.
        """
        query = self.db.query(IncidentReport).filter(
            IncidentReport.status == "pending"
        )

        if incident_type:
            query = query.filter(IncidentReport.incident_type == incident_type)

        total = query.count()
        reports = query.order_by(
            IncidentReport.evidence_quality_score.desc(),
            IncidentReport.created_at.asc()
        ).offset(offset).limit(limit).all()

        return reports, total

    def approve_report(
        self,
        report_id: str,
        moderator: User,
        validation_notes: Optional[str] = None
    ) -> IncidentReport:
        """
        Aprueba un reporte (status: pending -> validated).
        """
        report = self.incident_repo.get_by_id(report_id)

        if not report:
            raise ValueError(f"Reporte {report_id} no encontrado")

        if report.status != "pending":
            raise ValueError(
                f"Reporte no está pendiente (estado actual: {report.status})"
            )

        report.status = "validated"
        report.validated_at = datetime.utcnow()
        report.validated_by_user_id = moderator.id
        report.validation_notes = validation_notes

        self.db.commit()
        return report

    def reject_report(
        self,
        report_id: str,
        moderator: User,
        validation_notes: Optional[str] = None
    ) -> IncidentReport:
        """
        Rechaza un reporte (status: pending -> rejected).
        Requiere validation_notes (motivo del rechazo).
        """
        report = self.incident_repo.get_by_id(report_id)

        if not report:
            raise ValueError(f"Reporte {report_id} no encontrado")

        if report.status != "pending":
            raise ValueError(
                f"Reporte no está pendiente (estado actual: {report.status})"
            )

        if not validation_notes or validation_notes.strip() == "":
            raise ValueError("Debe proporcionar un motivo para rechazar el reporte")

        report.status = "rejected"
        report.validated_at = datetime.utcnow()
        report.validated_by_user_id = moderator.id
        report.validation_notes = validation_notes

        self.db.commit()
        return report

    def get_moderation_stats(self) -> dict:
        """
        Obtiene estadísticas de moderación.
        """
        total = self.db.query(IncidentReport).count()
        pending = self.db.query(IncidentReport).filter(
            IncidentReport.status == "pending"
        ).count()
        validated = self.db.query(IncidentReport).filter(
            IncidentReport.status == "validated"
        ).count()
        rejected = self.db.query(IncidentReport).filter(
            IncidentReport.status == "rejected"
        ).count()

        return {
            "total": total,
            "pending": pending,
            "validated": validated,
            "rejected": rejected,
        }

    def get_report_detail(self, report_id: str) -> IncidentReport:
        """
        Obtiene detalles completos de un reporte para moderación.
        """
        report = self.incident_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Reporte {report_id} no encontrado")
        return report
