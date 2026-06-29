from typing import Optional, List
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.report_document import ReportDocument
from app.interfaces.report_document_interface import IReportDocumentRepository


class ReportDocumentRepository(IReportDocumentRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        report_id: str,
        file_path: str,
        file_hash_sha256: str,
        file_type: str,
        file_size_bytes: int,
        original_filename: Optional[str] = None,
        description: Optional[str] = None,
        storage_type: str = "local",
    ) -> ReportDocument:
        """Crea un nuevo documento adjunto a un reporte"""
        document = ReportDocument(
            report_id=report_id,
            file_path=file_path,
            file_hash_sha256=file_hash_sha256,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            original_filename=original_filename,
            description=description,
            storage_type=storage_type,
            scan_status="pending",
        )
        self.db.add(document)
        self.db.flush()
        return document

    def hash_already_exists(self, file_hash_sha256: str, exclude_report_id: Optional[str] = None) -> bool:
        """
        Verifica si un archivo con este hash ya existe en el sistema.
        exclude_report_id: Si se proporciona, ignora documentos de ese reporte (para updates)
        """
        query = self.db.query(ReportDocument).filter(
            ReportDocument.file_hash_sha256 == file_hash_sha256
        )
        if exclude_report_id:
            query = query.filter(ReportDocument.report_id != exclude_report_id)
        return query.first() is not None

    def get_by_id(self, document_id: str) -> Optional[ReportDocument]:
        """Obtiene documento por ID."""
        return self.db.query(ReportDocument).filter(ReportDocument.id == document_id).first()

    def get_by_report(self, report_id: str) -> List[ReportDocument]:
        """Obtiene todos los documentos de un reporte ordenados por fecha."""
        return self.db.query(ReportDocument).filter(
            ReportDocument.report_id == report_id
        ).order_by(ReportDocument.uploaded_at.desc()).all()

    def hash_exists(self, file_hash_sha256: str) -> bool:
        """Verifica si un documento con este hash SHA-256 ya existe"""
        return self.db.query(ReportDocument).filter(
            ReportDocument.file_hash_sha256 == file_hash_sha256
        ).first() is not None

    def delete(self, document_id: str) -> bool:
        """Elimina un documento por ID"""
        document = self.get_by_id(document_id)
        if document:
            self.db.delete(document)
            return True
        return False

    def get_total_size_by_report(self, report_id: str) -> int:
        """Calcula el tamaño total en bytes de todos los documentos de un reporte"""
        result = self.db.query(
            func.sum(ReportDocument.file_size_bytes)
        ).filter(ReportDocument.report_id == report_id).scalar()
        return result if result is not None else 0

