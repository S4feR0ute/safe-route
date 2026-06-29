from sqlalchemy.orm import Session
from app.interfaces.user_interface import IUserRepository
from app.interfaces.incident_report_interface import IIncidentReportRepository
from app.interfaces.report_document_interface import IReportDocumentRepository
from app.interfaces.street_graph_interface import IStreetGraphDAO
from app.interfaces.crime_interface import ICrimeRepository
from app.interfaces.district_interface import IDistrictDAO
from app.interfaces.urban_context_interface import IUrbanContextDAO

from app.repositories.user_repository import UserRepository
from app.repositories.incident_report_repository import IncidentReportRepository
from app.repositories.report_document_repository import ReportDocumentRepository
from app.repositories.osmnx_street_graph_dao import OSMnxStreetGraphDAO
from app.repositories.sidpol_repository import SIDPOLCrimeRepository
from app.repositories.district_dao import OSMnxDistrictDAO
from app.repositories.osmnx_context_dao import OSMnxContextDAO
from app.repositories.risk_score_repository import RiskScoreRepository


class RepositoryFactory:
    """
    Factory centralizado para crear instancias de repositories.
    """

    @staticmethod
    def create_user_repository(db: Session) -> IUserRepository:
        """
        Crea un UserRepository para acceder a datos de usuarios.
        """
        return UserRepository(db)

    @staticmethod
    def create_incident_repository(db: Session) -> IIncidentReportRepository:
        """
        Crea un IncidentReportRepository para reportes de incidencias.
        """
        return IncidentReportRepository(db)

    @staticmethod
    def create_report_document_repository(db: Session) -> IReportDocumentRepository:
        """
        Crea un ReportDocumentRepository para documentos adjuntos a reportes.
        """
        return ReportDocumentRepository(db)

    @staticmethod
    def create_street_graph_dao(db: Session, network_type: str = "walk") -> IStreetGraphDAO:
        """
        Crea un OSMnxStreetGraphDAO para acceder a grafos de calles.
        """
        return OSMnxStreetGraphDAO(db=db, network_type=network_type)

    @staticmethod
    def create_crime_repository(db: Session) -> ICrimeRepository:
        """
        Crea un SIDPOLCrimeRepository para datos de criminalidad.
        """
        return SIDPOLCrimeRepository(db=db)

    @staticmethod
    def create_district_dao(db: Session) -> IDistrictDAO:
        """
        Crea un OSMnxDistrictDAO para acceder a distritos.
        """
        return OSMnxDistrictDAO(db=db)

    @staticmethod
    def create_urban_context_dao(db: Session) -> IUrbanContextDAO:
        """
        Crea un OSMnxContextDAO para acceder a contexto urbano (POIs).
        """
        return OSMnxContextDAO(db=db)

    @staticmethod
    def create_risk_score_repository(db: Session) -> RiskScoreRepository:
        """
        Crea un RiskScoreRepository para acceder a scores de riesgo.
        """
        return RiskScoreRepository(db=db)

    @staticmethod
    def create_routing_dependencies(db: Session) -> dict:
        """
        Crea todos los repositories necesarios para RoutingService.
        """
        return {
            'street_graph_dao': RepositoryFactory.create_street_graph_dao(db),
            'risk_score_repo': RepositoryFactory.create_risk_score_repository(db),
        }

    @staticmethod
    def create_scoring_dependencies(db: Session) -> dict:
        """
        Crea todos los repositories necesarios para ScoreCalculatorService.
        """
        return {
            'crime_repo': RepositoryFactory.create_crime_repository(db),
            'risk_score_repo': RepositoryFactory.create_risk_score_repository(db),
        }

    @staticmethod
    def create_report_dependencies(db: Session) -> dict:
        """
        Crea todos los repositories necesarios para el módulo de Reports (Sprint 5-6).
        """
        return {
            'user_repo': RepositoryFactory.create_user_repository(db),
            'incident_repo': RepositoryFactory.create_incident_repository(db),
            'document_repo': RepositoryFactory.create_report_document_repository(db),
        }
