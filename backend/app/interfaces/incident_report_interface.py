from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class IIncidentReportRepository(ABC):
    """Interfaz para repositories de reportes de incidencias"""

    @abstractmethod
    def create(
        self,
        incident_type: str,
        location_wkt: str,
        latitude: float,
        longitude: float,
        mode: int,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
        occurred_at=None,
    ):
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
    def get_pending_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        incident_type: Optional[str] = None,
    ) -> Tuple[List, int]:
        """Obtiene reportes pendientes paginados para moderación: (reportes, total)."""
        pass

    @abstractmethod
    def count_by_status(self) -> dict:
        """Cuenta reportes agrupados por estado (para stats de moderación)."""
        pass

    @abstractmethod
    def get_validated_reports(self, limit: int = 100) -> List:
        """Obtiene reportes validados."""
        pass

    @abstractmethod
    def get_validated_for_map(
        self,
        incident_type: Optional[str] = None,
        bbox: Optional[tuple] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[List, int]:
        """Obtiene reportes validados para el mapa público: (reportes, total)."""
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
    def update_documents_metadata(self, report_id: str, document_count: int, evidence_quality_score: float = 0.0):
        """Actualiza metadatos de documentos tras cargar/eliminar archivos."""
        pass

    @abstractmethod
    def count_reports_by_type_and_status(self, incident_type: str, status: str = "validated") -> int:
        """Cuenta reportes por tipo e estado."""
        pass

    @abstractmethod
    def delete(self, report_id: str) -> bool:
        """Elimina un reporte."""
        pass
