from abc import ABC, abstractmethod
from typing import Optional, List


class IReportDocumentRepository(ABC):
    """
    Interfaz para repositories de documentos adjuntos a reportes.
    Permite múltiples implementaciones (BD, S3, filesystem, etc.)
    """

    @abstractmethod
    def create(
        self,
        report_id: str,
        file_path: str,
        file_hash_sha256: str,
        file_type: str,
        file_size_bytes: int,
        original_filename: Optional[str] = None,
    ):
        """Crea un nuevo documento adjunto."""
        pass

    @abstractmethod
    def get_by_id(self, document_id: str):
        """Obtiene documento por ID."""
        pass

    @abstractmethod
    def get_by_report(self, report_id: str) -> List:
        """Obtiene todos los documentos de un reporte."""
        pass

    @abstractmethod
    def hash_exists(self, file_hash_sha256: str) -> bool:
        """Verifica si un documento con este hash ya existe (previene duplicados)."""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """Elimina un documento."""
        pass

    @abstractmethod
    def get_total_size_by_report(self, report_id: str) -> int:
        """Calcula el tamaño total en bytes de todos los documentos de un reporte."""
        pass
