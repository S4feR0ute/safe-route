from typing import Type, TypeVar, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.routing_service import RoutingService
from app.services.crime_analytics_service import CrimeAnalyticsService
from app.services.score_calculator_service import ScoreCalculatorService
from app.services.file_storage_service import FileStorageService
from app.repositories.factory import RepositoryFactory
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
        """Instancia única de AuthService."""
        return self._get_or_create(
            'auth_service',
            lambda: AuthService(db=self.db)
        )

    def get_routing_service(self) -> RoutingService:
        """Instancia única de RoutingService con DAOs inyectados."""
        def _create():
            graph_dao = RepositoryFactory.create_street_graph_dao(self.db)
            return RoutingService(db=self.db, graph_dao=graph_dao)

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
