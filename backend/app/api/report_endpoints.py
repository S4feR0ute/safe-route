import logging
from fastapi import APIRouter, UploadFile, File, Depends, status, Form
from sqlalchemy.orm import Session
from typing import Set, Optional

from app.db.session import get_db
from app.repositories.factory import RepositoryFactory
from app.services.file_storage_service import FileStorageService
from app.schemas.report_schemas import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    ReportResponse,
)
from app.core.error_handler import ErrorHandler
from app.core.service_container import ServiceContainer, get_service_container
from app.core.auth_helper import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReportResponse)
async def create_report(
    incident_type: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    container: ServiceContainer = Depends(get_service_container),
    current_user = Depends(get_current_user_optional),
):
    """Crea reporte con archivo opcional (multipart/form-data)."""
    try:
        report_service = container.get_report_service()
        document_repo = container.get_report_document_repository()
        incident_repo = container.get_incident_repository()

        if current_user:
            report = report_service.create_authenticated_report(
                incident_type=incident_type,
                latitude=latitude,
                longitude=longitude,
                user_id=current_user.id,
                description=description
            )
        else:
            report = report_service.create_anonymous_report(
                incident_type=incident_type,
                latitude=latitude,
                longitude=longitude,
                description=description
            )

        if file:
            try:
                storage_result = await FileStorageService.save_file(
                    file=file,
                    report_id=report.id,
                    current_report_size=0,
                )

                if document_repo.hash_already_exists(
                    storage_result.file_hash_sha256,
                    exclude_report_id=report.id
                ):
                    FileStorageService.delete_file(storage_result.file_path)
                    return ErrorHandler.conflict_error(
                        message="Archivo duplicado",
                        details={"file_hash": storage_result.file_hash_sha256}
                    )

                document_repo.create(
                    report_id=report.id,
                    file_path=storage_result.file_path,
                    file_hash_sha256=storage_result.file_hash_sha256,
                    file_type=storage_result.file_type,
                    file_size_bytes=storage_result.file_size_bytes,
                    original_filename=storage_result.original_filename,
                    storage_type="local",
                )

                documents = document_repo.get_by_report(report.id)
                quality_score = _calculate_quality_score(documents)
                incident_repo.update_documents_metadata(
                    report_id=report.id,
                    document_count=len(documents),
                    evidence_quality_score=quality_score,
                )

            except ValueError as e:
                container.db.rollback()
                return ErrorHandler.validation_error(message=str(e), field="file")

        container.db.commit()
        return ReportResponse.model_validate(report)

    except ValueError as e:
        container.db.rollback()
        return ErrorHandler.validation_error(message=str(e), field="report")
    except Exception as e:
        logger.exception(f"Report creation error: {type(e).__name__}")
        container.db.rollback()
        return ErrorHandler.internal_error(
            message="Error al crear el reporte"
        )


def _calculate_quality_score(documents: list) -> float:
    """
    Calcula la calidad de evidencia basada en cantidad y diversidad.
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


@router.post("/{report_id}/documents", response_model=DocumentUploadResponse)
async def upload_report_document(
    report_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    try:
        incident_repo = RepositoryFactory.create_incident_repository(db)
        document_repo = RepositoryFactory.create_report_document_repository(db)

        report = incident_repo.get_by_id(report_id)
        if not report:
            return ErrorHandler.not_found(f"Reporte {report_id}")

        current_size = document_repo.get_total_size_by_report(report_id)

        storage_result = await FileStorageService.save_file(
            file=file,
            report_id=report_id,
            current_report_size=current_size,
        )

        if document_repo.hash_already_exists(
            storage_result.file_hash_sha256,
            exclude_report_id=report_id
        ):
            return ErrorHandler.conflict_error(
                message="Archivo duplicado (mismo contenido ya existe)",
                details={"file_hash": storage_result.file_hash_sha256}
            )

        document = document_repo.create(
            report_id=report_id,
            file_path=storage_result.file_path,
            file_hash_sha256=storage_result.file_hash_sha256,
            file_type=storage_result.file_type,
            file_size_bytes=storage_result.file_size_bytes,
            original_filename=storage_result.original_filename,
            storage_type="local",
        )

        documents = document_repo.get_by_report(report_id)
        quality_score = _calculate_quality_score(documents)

        incident_repo.update_documents_metadata(
            report_id=report_id,
            document_count=len(documents),
            evidence_quality_score=quality_score,
        )

        db.commit()

        return DocumentUploadResponse(
            document_id=document.id,
            report_id=document.report_id,
            file_type=document.file_type,
            file_size_bytes=document.file_size_bytes,
            original_filename=document.original_filename,
            file_path=storage_result.file_path,
            uploaded_at=document.uploaded_at,
        )

    except ValueError as e:
        return ErrorHandler.validation_error(message=str(e), field="file")
    except Exception as e:
        logger.exception(f"Document upload error: {type(e).__name__}")
        db.rollback()
        return ErrorHandler.internal_error(
            message="Error al cargar documento"
        )


@router.get("/{report_id}/documents", response_model=DocumentListResponse)
async def get_report_documents(
    report_id: str,
    db: Session = Depends(get_db),
):
    try:
        incident_repo = RepositoryFactory.create_incident_repository(db)
        document_repo = RepositoryFactory.create_report_document_repository(db)

        report = incident_repo.get_by_id(report_id)
        if not report:
            return ErrorHandler.not_found(f"Reporte {report_id}")

        documents = document_repo.get_by_report(report_id)
        total_size = document_repo.get_total_size_by_report(report_id)

        return DocumentListResponse(
            report_id=report_id,
            total_documents=len(documents),
            total_size_bytes=total_size,
            documents=[DocumentResponse.model_validate(doc) for doc in documents]
        )

    except Exception as e:
        logger.exception(f"Get documents error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al obtener documentos"
        )


@router.delete("/{report_id}/documents/{document_id}")
async def delete_report_document(
    report_id: str,
    document_id: str,
    db: Session = Depends(get_db),
):
    try:
        document_repo = RepositoryFactory.create_report_document_repository(db)
        incident_repo = RepositoryFactory.create_incident_repository(db)

        document = document_repo.get_by_id(document_id)
        if not document:
            return ErrorHandler.not_found(f"Documento {document_id}")

        if document.report_id != report_id:
            return ErrorHandler.authorization_error(
                message="El documento no pertenece a este reporte"
            )

        FileStorageService.delete_file(document.file_path)
        document_repo.delete(document_id)

        documents = document_repo.get_by_report(report_id)
        quality_score = _calculate_quality_score(documents)

        incident_repo.update_documents_metadata(
            report_id=report_id,
            document_count=len(documents),
            evidence_quality_score=quality_score,
        )

        db.commit()

        return {"message": "Documento eliminado correctamente"}

    except Exception as e:
        logger.exception(f"Delete document error: {type(e).__name__}")
        db.rollback()
        return ErrorHandler.internal_error(
            message="Error al eliminar documento"
        )
