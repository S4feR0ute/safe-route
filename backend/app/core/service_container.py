from typing import Any, Callable, Dict

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.factory import RepositoryFactory
from app.interfaces.user_interface import IUserRepository
from app.interfaces.incident_report_interface import IIncidentReportRepository
from app.interfaces.report_document_interface import IReportDocumentRepository
from app.interfaces.risk_score_interface import IRiskScoreRepository
from app.services.auth_service import AuthService
from app.services.routing_service import RoutingService
from app.services.nominatim_service import NominatimService
from app.services.report_service import ReportService
from app.services.moderation_service import ModerationService
from app.services.file_storage_service import FileStorageService
from app.services.crime_analytics_service import CrimeAnalyticsService
from app.services.score_calculator_service import ScoreCalculatorService


class ServiceContainer:
    """
    Contenedor IoC con patrón Singleton para servicios.
    Resuelve dependencias automáticamente y cachea instancias.
    """

    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, Any] = {}

    def _get_or_create(self, key: str, factory: Callable[[], Any]) -> Any:
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    def clear(self) -> None:
        """Limpia el caché (útil para tests)."""
        self._cache.clear()

    # Repositorios

    def get_user_repository(self) -> IUserRepository:
        return self._get_or_create(
            "user_repo",
            lambda: RepositoryFactory.create_user_repository(self.db),
        )

    def get_incident_repository(self) -> IIncidentReportRepository:
        return self._get_or_create(
            "incident_repo",
            lambda: RepositoryFactory.create_incident_repository(self.db),
        )

    def get_report_document_repository(self) -> IReportDocumentRepository:
        return self._get_or_create(
            "document_repo",
            lambda: RepositoryFactory.create_report_document_repository(self.db),
        )

    def get_risk_score_repository(self) -> IRiskScoreRepository:
        return self._get_or_create(
            "risk_score_repo",
            lambda: RepositoryFactory.create_risk_score_repository(self.db),
        )

    # Servicios

    def get_auth_service(self) -> AuthService:
        return self._get_or_create(
            "auth_service",
            lambda: AuthService(
                db=self.db,
                user_repo=self.get_user_repository(),
            ),
        )

    def get_routing_service(self) -> RoutingService:
        return self._get_or_create(
            "routing_service",
            lambda: RoutingService(
                db=self.db,
                graph_dao=RepositoryFactory.create_street_graph_dao(self.db),
                score_repo=self.get_risk_score_repository(),
            ),
        )

    def get_nominatim_service(self) -> NominatimService:
        return self._get_or_create(
            "nominatim_service",
            lambda: NominatimService(),
        )

    def get_report_service(self) -> ReportService:
        return self._get_or_create(
            "report_service",
            lambda: ReportService(
                db=self.db,
                incident_repo=self.get_incident_repository(),
                document_repo=self.get_report_document_repository(),
            ),
        )

    def get_moderation_service(self) -> ModerationService:
        return self._get_or_create(
            "moderation_service",
            lambda: ModerationService(
                db=self.db,
                incident_repo=self.get_incident_repository(),
            ),
        )

    def get_crime_analytics_service(self) -> CrimeAnalyticsService:
        return self._get_or_create(
            "crime_analytics_service",
            lambda: CrimeAnalyticsService(db=self.db),
        )

    def get_score_calculator_service(self) -> ScoreCalculatorService:
        return self._get_or_create(
            "score_calculator_service",
            lambda: ScoreCalculatorService(db=self.db),
        )
    
    @staticmethod
    def get_file_storage_service() -> type:
        return FileStorageService


def get_service_container(db: Session = Depends(get_db)) -> ServiceContainer:
    """Dependencia FastAPI para obtener el contenedor de servicios."""
    return ServiceContainer(db)
