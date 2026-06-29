from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from geoalchemy2.functions import ST_DWithin, ST_GeomFromText
from geoalchemy2.elements import WKTElement
from app.models.incident_report import IncidentReport
from app.interfaces.incident_report_interface import IIncidentReportRepository


class IncidentReportRepository(IIncidentReportRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident_type: str, location_wkt: str, mode: int, user_id: Optional[int] = None, description: Optional[str] = None) -> IncidentReport:
        """
        Crea un nuevo reporte.
        location_wkt: formato WKT, ej: 'SRID=4326;POINT(-77.0428 -12.0464)'
        """
        report = IncidentReport(
            incident_type=incident_type,
            location=WKTElement(location_wkt, srid=4326),
            mode=mode,
            user_id=user_id,
            description=description,
        )
        self.db.add(report)
        self.db.flush()
        return report

    def get_by_id(self, report_id: str) -> Optional[IncidentReport]:
        """Obtiene reporte por ID."""
        return self.db.query(IncidentReport).filter(IncidentReport.id == report_id).first()

    def get_by_user(self, user_id: int) -> List[IncidentReport]:
        """Obtiene todos los reportes de un usuario."""
        return self.db.query(IncidentReport).filter(
            IncidentReport.user_id == user_id
        ).order_by(IncidentReport.created_at.desc()).all()

    def get_pending_reports(self, limit: int = 100) -> List[IncidentReport]:
        """Obtiene reportes pendientes de validación (modo 3)."""
        return self.db.query(IncidentReport).filter(
            IncidentReport.status == "pending",
            IncidentReport.mode == 3,
        ).order_by(IncidentReport.created_at.asc()).limit(limit).all()

    def get_validated_reports(self, limit: int = 100) -> List[IncidentReport]:
        """Obtiene reportes validados (para integrar al score)."""
        return self.db.query(IncidentReport).filter(
            IncidentReport.status == "validated"
        ).order_by(IncidentReport.validated_at.desc()).limit(limit).all()

    def get_near_location(self, longitude: float, latitude: float, radius_m: int = 500, status: Optional[str] = "validated") -> List[IncidentReport]:
        """Obtiene reportes validados cerca de una ubicación"""
        query = self.db.query(IncidentReport)

        if status:
            query = query.filter(IncidentReport.status == status)

        # ST_DWithin: distancia en metros usando geografía
        point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
        query = query.filter(
            ST_DWithin(
                IncidentReport.location.cast(ST_GeomFromText),
                ST_GeomFromText(point_wkt, 4326),
                radius_m
            )
        )
        return query.all()

    def update_report_status(self, report_id: str, status: str, validated_by_user_id: Optional[int] = None) -> Optional[IncidentReport]:
        """Actualiza estado de reporte (pending -> validated/rejected)"""
        report = self.get_by_id(report_id)
        if report:
            report.status = status
            report.validated_by_user_id = validated_by_user_id
            if status == "validated":
                report.validated_at = datetime.utcnow()
        return report

    def count_reports_by_type_and_status(self, incident_type: str, status: str = "validated") -> int:
        """Cuenta reportes por tipo e estado (para análisis)."""
        return self.db.query(IncidentReport).filter(
            and_(
                IncidentReport.incident_type == incident_type,
                IncidentReport.status == status
            )
        ).count()

    def update_documents_metadata(self, report_id: str, document_count: int, evidence_quality_score: float = 0.0) -> Optional[IncidentReport]:
        """Actualiza metadatos de documentos después de cargar/eliminar archivos"""
        report = self.get_by_id(report_id)
        if report:
            report.has_documents = document_count > 0
            report.document_count = document_count
            report.evidence_quality_score = min(100.0, max(0.0, evidence_quality_score))
            return report
        return None

    def get_reports_with_documents(self, limit: int = 100) -> List[IncidentReport]:
        """Obtiene reportes que tienen documentos adjuntos."""
        return self.db.query(IncidentReport).filter(
            IncidentReport.has_documents == True
        ).order_by(IncidentReport.created_at.desc()).limit(limit).all()

    def delete(self, report_id: str) -> bool:
        """Elimina un reporte (soft o hard según política)."""
        report = self.get_by_id(report_id)
        if report:
            self.db.delete(report)
            return True
        return False
