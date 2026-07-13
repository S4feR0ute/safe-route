from sqlalchemy.orm import Session
from app.interfaces.street_graph_interface import IStreetGraphDAO

from app.repositories.user_repository import UserRepository
from app.repositories.incident_report_repository import IncidentReportRepository
from app.repositories.report_document_repository import ReportDocumentRepository
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO
from app.repositories.risk_score_repository import RiskScoreRepository


class RepositoryFactory:
    @staticmethod
    def create_user_repository(db: Session) -> UserRepository:
        """Crea un UserRepository para acceder a datos de usuarios."""
        return UserRepository(db)

    @staticmethod
    def create_incident_repository(db: Session) -> IncidentReportRepository:
        """Crea un IncidentReportRepository para reportes de incidencias."""
        return IncidentReportRepository(db)

    @staticmethod
    def create_report_document_repository(db: Session) -> ReportDocumentRepository:
        """Crea un ReportDocumentRepository para documentos adjuntos a reportes."""
        return ReportDocumentRepository(db)

    @staticmethod
    def create_street_graph_dao(db: Session, network_type: str = "walk") -> IStreetGraphDAO:
        """Crea un OSMnxStreetGraphDAO para acceder a grafos de calles."""
        return OSMnxStreetGraphDAO(db=db, network_type=network_type)

    @staticmethod
    def create_risk_score_repository(db: Session) -> RiskScoreRepository:
        """Crea un RiskScoreRepository para acceder a scores de riesgo."""
        return RiskScoreRepository(db=db)
