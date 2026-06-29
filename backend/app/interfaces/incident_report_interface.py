from abc import ABC, abstractmethod
from typing import Optional, List


class IIncidentReportRepository(ABC):
    """Interfaz para repositories de reportes de incidencias"""

    @abstractmethod
    def create(self, incident_type: str, location_wkt: str, mode: int, user_id: Optional[int] = None, description: Optional[str] = None):
        """Crea un nuevo reporte."""
        pass

    @abstractmethod
    def get_by_id(self, report_id: str):
        """Obtiene reporte por ID."""
        pass

    @abstractmethod
    def get_by_user(self, user_id: int) -> List:
        """Obtiene todos los reportes de un usuario."""
        pass

    @abstractmethod
    def get_pending_reports(self, limit: int = 100) -> List:
        """Obtiene reportes pendientes de validación (modo 3)."""
        pass

    @abstractmethod
    def get_validated_reports(self, limit: int = 100) -> List:
        """Obtiene reportes validados."""
        pass

    @abstractmethod
    def get_near_location(self, longitude: float, latitude: float, radius_m: int = 500, status: Optional[str] = "validated") -> List:
        """Obtiene reportes validados cerca de una ubicación."""
        pass

    @abstractmethod
    def update_report_status(self, report_id: str, status: str, validated_by_user_id: Optional[int] = None):
        """Actualiza estado de reporte."""
        pass

    @abstractmethod
    def count_reports_by_type_and_status(self, incident_type: str, status: str = "validated") -> int:
        """Cuenta reportes por tipo e estado."""
        pass

    @abstractmethod
    def delete(self, report_id: str) -> bool:
        """Elimina un reporte."""
        pass
