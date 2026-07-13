from typing import Any, Callable, Dict

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.factory import RepositoryFactory
from app.repositories.user_repository import UserRepository
from app.repositories.incident_report_repository import IncidentReportRepository
from app.repositories.report_document_repository import ReportDocumentRepository
from app.repositories.risk_score_repository import RiskScoreRepository
from app.services.auth_service import AuthService
from app.services.routing_service import RoutingService
from app.services.nominatim_service import NominatimService
from app.services.report_service import ReportService
from app.services.moderation_service import ModerationService
from app.services.file_storage_service import FileStorageService


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
        self._cache.clear()

    # Repositorios

    def get_user_repository(self) -> UserRepository:
        return self._get_or_create(
            "user_repo",
            lambda: RepositoryFactory.create_user_repository(self.db),
        )

    def get_incident_repository(self) -> IncidentReportRepository:
        return self._get_or_create(
            "incident_repo",
            lambda: RepositoryFactory.create_incident_repository(self.db),
        )

    def get_report_document_repository(self) -> ReportDocumentRepository:
        return self._get_or_create(
            "document_repo",
            lambda: RepositoryFactory.create_report_document_repository(self.db),
        )

    def get_risk_score_repository(self) -> RiskScoreRepository:
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
                storage_service=self.get_file_storage_service(),
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

    def get_file_storage_service(self) -> FileStorageService:
        return self._get_or_create(
            "file_storage_service",
            lambda: FileStorageService(),
        )


def get_service_container(db: Session = Depends(get_db)) -> ServiceContainer:
    """Dependencia FastAPI para obtener el contenedor de servicios."""
    return ServiceContainer(db)
