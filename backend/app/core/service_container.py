from typing import Type, TypeVar, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.routing_service import RoutingService
from app.services.crime_analytics_service import CrimeAnalyticsService
from app.services.score_calculator_service import ScoreCalculatorService
from app.services.file_storage_service import FileStorageService
from app.services.report_service import ReportService
from app.repositories.factory import RepositoryFactory
from app.interfaces.user_interface import IUserRepository
from app.interfaces.incident_report_interface import IIncidentReportRepository
from app.interfaces.report_document_interface import IReportDocumentRepository
from app.interfaces.risk_score_interface import IRiskScoreRepository
from app.db.session import get_db

T = TypeVar('T')


class ServiceContainer:
    """
    Contenedor IoC con patrón Singleton para servicios.
    Resuelve dependencias automáticamente y cachea instancias.
    """

    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, Any] = {}

    def _get_or_create(self, key: str, factory_func) -> Any:
        """Helper para patrón Singleton con lazy initialization."""
        if key not in self._cache:
            self._cache[key] = factory_func()
        return self._cache[key]

    def get_auth_service(self) -> AuthService:
        """Instancia única de AuthService con UserRepository inyectado."""
        def _create():
            user_repo = self.get_user_repository()
            return AuthService(db=self.db, user_repo=user_repo)

        return self._get_or_create('auth_service', _create)

    def get_routing_service(self) -> RoutingService:
        """Instancia única de RoutingService con DAOs inyectados."""
        def _create():
            graph_dao = RepositoryFactory.create_street_graph_dao(self.db)
            score_repo = self.get_risk_score_repository()
            return RoutingService(db=self.db, graph_dao=graph_dao, score_repo=score_repo)

        return self._get_or_create('routing_service', _create)

    def get_crime_analytics_service(self) -> CrimeAnalyticsService:
        """Instancia única de CrimeAnalyticsService."""
        def _create():
            crime_repo = RepositoryFactory.create_crime_repository(self.db)
            return CrimeAnalyticsService(crime_repo=crime_repo)

        return self._get_or_create('crime_analytics', _create)

    def get_score_calculator_service(self) -> ScoreCalculatorService:
        """Instancia única de ScoreCalculatorService."""
        return self._get_or_create(
            'score_calculator',
            lambda: ScoreCalculatorService(db=self.db)
        )

    def get_report_service(self) -> ReportService:
        """Instancia única de ReportService con repositorio inyectado."""
        def _create():
            incident_repo = self.get_incident_repository()
            return ReportService(db=self.db, incident_repo=incident_repo)

        return self._get_or_create('report_service', _create)

    def get_incident_repository(self) -> IIncidentReportRepository:
        """Instancia única cacheada de IncidentReportRepository."""
        return self._get_or_create(
            'incident_repo',
            lambda: RepositoryFactory.create_incident_repository(self.db)
        )

    def get_report_document_repository(self) -> IReportDocumentRepository:
        """Instancia única cacheada de ReportDocumentRepository."""
        return self._get_or_create(
            'document_repo',
            lambda: RepositoryFactory.create_report_document_repository(self.db)
        )

    def get_user_repository(self) -> IUserRepository:
        """Instancia única cacheada de UserRepository."""
        return self._get_or_create(
            'user_repo',
            lambda: RepositoryFactory.create_user_repository(self.db)
        )

    def get_risk_score_repository(self) -> IRiskScoreRepository:
        """Instancia única cacheada de RiskScoreRepository."""
        return self._get_or_create(
            'risk_score_repo',
            lambda: RepositoryFactory.create_risk_score_repository(self.db)
        )

    @staticmethod
    def get_file_storage_service() -> type:
        """FileStorageService es stateless - devuelve la clase."""
        return FileStorageService

    def clear(self):
        """Limpia caché (útil para tests)."""
        self._cache.clear()


def get_service_container(db: Session = Depends(get_db)) -> ServiceContainer:
    """Dependencia FastAPI para obtener el contenedor de servicios."""
    return ServiceContainer(db)
