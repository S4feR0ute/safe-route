from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.factory import RepositoryFactory
from app.models.incident_report import IncidentReport
from app.core.validators import CoordinateValidator


class ReportService:
    """
    Servicio de reportes de incidentes.
    Maneja creación de reportes anónimos (modo 1) y autenticados (modo 2).
    """

    def __init__(self, db: Session, incident_repo=None):
        self.db = db
        self.incident_repo = incident_repo or RepositoryFactory.create_incident_repository(db)

    def create_anonymous_report(
        self,
        incident_type: str,
        latitude: float,
        longitude: float,
        description: Optional[str] = None
    ) -> IncidentReport:
        """
        Crea un reporte anónimo (modo 1).
        No requiere autenticación.
        """
        lat, lon = CoordinateValidator.validate(latitude, longitude)

        location_wkt = f"SRID=4326;POINT({lon} {lat})"

        report = self.incident_repo.create(
            incident_type=incident_type,
            location_wkt=location_wkt,
            latitude=lat,
            longitude=lon,
            mode=1,
            user_id=None,
            description=description
        )

        return report

    def create_authenticated_report(
        self,
        incident_type: str,
        latitude: float,
        longitude: float,
        user_id: int,
        description: Optional[str] = None
    ) -> IncidentReport:
        """
        Crea un reporte autenticado (modo 2).
        Requiere user_id válido.
        """
        lat, lon = CoordinateValidator.validate(latitude, longitude)

        location_wkt = f"SRID=4326;POINT({lon} {lat})"

        report = self.incident_repo.create(
            incident_type=incident_type,
            location_wkt=location_wkt,
            latitude=lat,
            longitude=lon,
            mode=2,
            user_id=user_id,
            description=description
        )

        return report
