from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.elements import WKTElement
from app.models.incident_report import IncidentReport


class IncidentReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        incident_type: str,
        location_wkt: str,
        latitude: float,
        longitude: float,
        mode: int,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        occurred_at: Optional[datetime] = None
    ) -> IncidentReport:
        """Crea un nuevo reporte de incidencia."""
        report = IncidentReport(
            incident_type=incident_type,
            location=WKTElement(location_wkt, srid=4326),
            latitude=latitude,
            longitude=longitude,
            mode=mode,
            user_id=user_id,
            description=description,
            occurred_at=occurred_at,
        )
        self.db.add(report)
        self.db.flush()
        return report

    def get_by_id(self, report_id: str) -> Optional[IncidentReport]:
        """Obtiene reporte por ID."""
        return self.db.query(IncidentReport).filter(IncidentReport.id == report_id).first()

    def get_pending_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        incident_type: Optional[str] = None,
    ) -> Tuple[List[IncidentReport], int]:
        """Reportes pendientes paginados para la cola de moderación: (reportes, total)."""
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

    def count_by_status(self) -> dict:
        """Cuenta reportes agrupados por estado."""
        rows = self.db.query(
            IncidentReport.status, func.count(IncidentReport.id)
        ).group_by(IncidentReport.status).all()
        counts = {status: count for status, count in rows}
        return {
            "total": sum(counts.values()),
            "pending": counts.get("pending", 0),
            "validated": counts.get("validated", 0),
            "rejected": counts.get("rejected", 0),
        }

    def get_validated_for_map(
        self,
        incident_type: Optional[str] = None,
        bbox: Optional[tuple] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[List[IncidentReport], int]:
        """Reportes validados para el mapa público: (reportes, total)."""
        query = self.db.query(IncidentReport).filter(
            IncidentReport.status == "validated"
        )
        if incident_type:
            query = query.filter(IncidentReport.incident_type == incident_type)
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            query = query.filter(
                IncidentReport.longitude.between(min_lon, max_lon),
                IncidentReport.latitude.between(min_lat, max_lat),
            )

        total = query.count()
        reports = query.order_by(
            IncidentReport.created_at.desc()
        ).offset(offset).limit(limit).all()
        return reports, total

    def update_documents_metadata(
            self,
            report_id: str,
            document_count: int,
            evidence_quality_score: float = 0.0
        ) -> Optional[IncidentReport]:
        """Actualiza metadatos de documentos después de cargar/eliminar archivos."""
        report = self.get_by_id(report_id)
        if report:
            report.has_documents = document_count > 0
            report.document_count = document_count
            report.evidence_quality_score = min(100.0, max(0.0, evidence_quality_score))
            if report.user_id is not None:
                report.mode = 3 if document_count > 0 else 2
            return report
        return None

    def delete(self, report_id: str) -> bool:
        """Elimina un reporte (soft o hard según política)."""
        report = self.get_by_id(report_id)
        if report:
            self.db.delete(report)
            return True
        return False
