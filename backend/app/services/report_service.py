from datetime import datetime, timedelta
from typing import Optional, List, Set, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories.factory import RepositoryFactory
from app.models.incident_report import IncidentReport
from app.models.report_document import ReportDocument
from app.models.user import User
from app.interfaces.incident_report_interface import IIncidentReportRepository
from app.interfaces.report_document_interface import IReportDocumentRepository
from app.services.file_storage_service import FileStorageService
from app.core.validators import CoordinateValidator
from app.core.exceptions import ReportNotFoundError, DuplicateFileError
from app.db.transactions import transaction_no_close


class ReportService:
    """
    Servicio de reportes de incidentes (RF-14 a RF-16, RF-19).

    Modos de reporte:
      1 = anónimo: ubicación + tipo + descripción (sin fecha ni archivos)
      2 = autenticado: modo 1 + fecha del incidente (occurred_at)
      3 = autenticado + documentos adjuntos

    Cada método público es la frontera transaccional.
    """

    def __init__(
        self,
        db: Session,
        incident_repo: IIncidentReportRepository = None,
        document_repo: IReportDocumentRepository = None,
    ):
        self.db = db
        self.incident_repo = incident_repo or RepositoryFactory.create_incident_repository(db)
        self.document_repo = document_repo or RepositoryFactory.create_report_document_repository(db)

    async def create_report(
        self,
        incident_type: str,
        latitude: float,
        longitude: float,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        occurred_at: Optional[datetime] = None,
        file: Optional[UploadFile] = None,
    ) -> IncidentReport:
        """
        Crea un reporte. El modo se deduce: 1 (anónimo), 2 (autenticado),
        3 (autenticado + archivo). Todo dentro de una sola transacción.
        """
        if user_id is None:
            if file is not None:
                raise ValueError(
                    "Adjuntar archivos requiere una cuenta (modo 3). "
                    "Inicia sesión o envía el reporte sin archivo."
                )
            if occurred_at is not None:
                raise ValueError(
                    "Indicar la fecha del incidente requiere una cuenta (modo 2). "
                    "Inicia sesión o envía el reporte sin fecha."
                )

        if occurred_at is not None and occurred_at > datetime.utcnow() + timedelta(minutes=5):
            raise ValueError("La fecha del incidente no puede estar en el futuro")

        lat, lon = CoordinateValidator.validate(latitude, longitude)
        mode = 3 if file is not None else (2 if user_id is not None else 1)

        saved_file_path = None
        try:
            with transaction_no_close(self.db):
                report = self.incident_repo.create(
                    incident_type=incident_type,
                    location_wkt=f"SRID=4326;POINT({lon} {lat})",
                    latitude=lat,
                    longitude=lon,
                    mode=mode,
                    user_id=user_id,
                    description=description,
                    occurred_at=occurred_at,
                )

                if file:
                    storage_result = await FileStorageService.save_file(
                        file=file,
                        report_id=report.id,
                        current_report_size=0,
                    )
                    saved_file_path = storage_result.file_path
                    self._attach_document(report.id, storage_result)

            return report

        except Exception:
            if saved_file_path:
                FileStorageService.delete_file(saved_file_path)
            raise

    async def add_document(self, report_id: str, file: UploadFile, user: User) -> ReportDocument:
        """
        Adjunta un documento a un reporte existente (lo promueve a modo 3).
        Solo el dueño del reporte puede adjuntar; los reportes anónimos no
        admiten documentos.
        """
        report = self._get_report_or_raise(report_id)

        if report.user_id is None:
            raise PermissionError("Un reporte anónimo (modo 1) no admite documentos")
        if report.user_id != user.id:
            raise PermissionError("Solo el autor del reporte puede adjuntar documentos")

        current_size = self.document_repo.get_total_size_by_report(report.id)
        storage_result = await FileStorageService.save_file(
            file=file,
            report_id=report.id,
            current_report_size=current_size,
        )

        try:
            with transaction_no_close(self.db):
                document = self._attach_document(report.id, storage_result)
            return document
        except Exception:
            FileStorageService.delete_file(storage_result.file_path)
            raise

    def get_documents(self, report_id: str, user: User) -> Tuple[List[ReportDocument], int]:
        """Lista los documentos de un reporte: (documentos, tamaño total en bytes)."""
        report = self._get_report_or_raise(report_id)
        self._require_owner_or_moderator(report, user)

        documents = self.document_repo.get_by_report(report.id)
        total_size = self.document_repo.get_total_size_by_report(report.id)
        return documents, total_size

    def remove_document(self, report_id: str, document_id: str, user: User) -> None:
        """Elimina un documento (autor o moderador). Si era el último, el reporte vuelve a modo 2."""
        report = self._get_report_or_raise(report_id)
        self._require_owner_or_moderator(report, user)

        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise ReportNotFoundError(f"Documento {document_id} no encontrado")

        if document.report_id != report_id:
            raise PermissionError("El documento no pertenece a este reporte")

        with transaction_no_close(self.db):
            FileStorageService.delete_file(document.file_path)
            self.document_repo.delete(document_id)
            self._refresh_documents_metadata(report_id)

    def get_public_reports(
        self,
        incident_type: Optional[str] = None,
        bbox: Optional[tuple] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[List[IncidentReport], int]:
        """Reportes para el mapa público. Solo devuelve reportesvalidados."""
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        return self.incident_repo.get_validated_for_map(
            incident_type=incident_type,
            bbox=bbox,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def _require_owner_or_moderator(report: IncidentReport, user: User) -> None:
        is_moderator = user.user_type in ("moderator", "admin")
        if not is_moderator and report.user_id != user.id:
            raise PermissionError("No tienes permisos sobre los documentos de este reporte")

    def _get_report_or_raise(self, report_id: str) -> IncidentReport:
        report = self.incident_repo.get_by_id(report_id)
        if not report:
            raise ReportNotFoundError(f"Reporte {report_id} no encontrado")
        return report

    def _attach_document(self, report_id: str, storage_result) -> ReportDocument:
        """Registra un archivo ya guardado: dedup por hash, alta y metadatos."""
        if self.document_repo.hash_already_exists(
            storage_result.file_hash_sha256,
            exclude_report_id=report_id,
        ):
            FileStorageService.delete_file(storage_result.file_path)
            raise DuplicateFileError(
                f"Archivo duplicado (hash: {storage_result.file_hash_sha256})"
            )

        document = self.document_repo.create(
            report_id=report_id,
            file_path=storage_result.file_path,
            file_hash_sha256=storage_result.file_hash_sha256,
            file_type=storage_result.file_type,
            file_size_bytes=storage_result.file_size_bytes,
            original_filename=storage_result.original_filename,
            storage_type="local",
        )
        self._refresh_documents_metadata(report_id)
        return document

    def _refresh_documents_metadata(self, report_id: str) -> None:
        documents = self.document_repo.get_by_report(report_id)
        self.incident_repo.update_documents_metadata(
            report_id=report_id,
            document_count=len(documents),
            evidence_quality_score=self._calculate_quality_score(documents),
        )

    @staticmethod
    def _calculate_quality_score(documents: list) -> float:
        """
        Calidad de evidencia según cantidad y diversidad de documentos.
        Base: 20 puntos por documento + bonus de 10 si hay diversidad.
        """
        quality_score = len(documents) * 20.0

        if documents:
            evidence_types: Set[str] = set()
            for doc in documents:
                if "image" in doc.file_type:
                    evidence_types.add("photo")
                elif "video" in doc.file_type:
                    evidence_types.add("video")
                elif "audio" in doc.file_type:
                    evidence_types.add("audio")
                elif doc.file_type == "application/pdf":
                    evidence_types.add("document")

            if len(evidence_types) > 1:
                quality_score += 10.0

        return min(100.0, quality_score)
