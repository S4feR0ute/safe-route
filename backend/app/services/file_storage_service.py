import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import UploadFile

from app.core.file_config import FileConfig


class FileStorageResult:
    """Resultado de guardar un archivo."""

    def __init__(
        self,
        file_path: str,
        file_hash_sha256: str,
        file_size_bytes: int,
        original_filename: str,
        file_type: str,
    ):
        self.file_path = file_path
        self.file_hash_sha256 = file_hash_sha256
        self.file_size_bytes = file_size_bytes
        self.original_filename = original_filename
        self.file_type = file_type


class FileStorageService:
    """
    Servicio para almacenar archivos de reportes.
    Maneja validación, guardado y generación de hashes.
    """

    @staticmethod
    async def save_file( file: UploadFile, report_id: str, current_report_size: int = 0) -> FileStorageResult:
        # 1. Leer contenido del archivo
        file_content = await file.read()
        file_size = len(file_content)

        # 2. Validar MIME type
        mime_type = file.content_type or "application/octet-stream"
        if not FileConfig.is_mime_type_allowed(mime_type):
            raise ValueError(
                f"Tipo de archivo no permitido: {mime_type}. "
                f"Permitidos: {', '.join(FileConfig.ALLOWED_MIME_TYPES.keys())}"
            )

        # 3. Validar tamaño individual
        is_valid, error_msg = FileConfig.validate_file_size(file_size)
        if not is_valid:
            raise ValueError(error_msg)

        # 4. Validar tamaño total del reporte
        is_valid, error_msg = FileConfig.validate_report_total_size(
            current_report_size,
            file_size
        )
        if not is_valid:
            raise ValueError(error_msg)

        # 5. Calcular SHA-256 hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # 6. Generar nombre de archivo seguro (usar hash para evitar colisiones)
        extension = FileConfig.get_file_extension(mime_type)
        safe_filename = f"{file_hash[:16]}.{extension}"

        # 7. Crear directorio de reporte
        upload_dir = FileConfig.get_upload_dir_for_report(report_id)

        # 8. Guardar archivo
        file_path = upload_dir / safe_filename
        file_path.write_bytes(file_content)

        # 9. Retornar resultado
        relative_path = str(file_path.relative_to(FileConfig.UPLOAD_BASE_DIR))

        return FileStorageResult(
            file_path=relative_path,
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            original_filename=file.filename or "unknown",
            file_type=mime_type,
        )

    @staticmethod
    def get_file_path(relative_path: str) -> Path:
        """Obtiene la ruta completa de un archivo."""
        return FileConfig.UPLOAD_BASE_DIR / relative_path

    @staticmethod
    def file_exists(relative_path: str) -> bool:
        """Verifica si un archivo existe."""
        file_path = FileStorageService.get_file_path(relative_path)
        return file_path.exists()

    @staticmethod
    def delete_file(relative_path: str) -> bool:
        """Elimina un archivo del almacenamiento."""
        try:
            file_path = FileStorageService.get_file_path(relative_path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            raise ValueError(f"Error al eliminar archivo: {str(e)}")

    @staticmethod
    def get_download_url(relative_path: str) -> str:
        """Genera URL para descargar un archivo."""
        return f"/api/v1/downloads/{relative_path}"
