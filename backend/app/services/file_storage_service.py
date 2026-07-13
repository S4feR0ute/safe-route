import hashlib
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile

from app.core.file_config import FileConfig
from app.services.storage import StorageBackend, LocalStorageBackend


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
    Orquesta el almacenamiento de archivos de reportes: valida (MIME, tamaño),
    calcula el hash y delega el IO físico a un StorageBackend (Strategy).
    """

    def __init__(self, backend: StorageBackend = None):
        self.backend = backend or LocalStorageBackend()

    async def save_file(self, file: UploadFile, report_id: str, current_report_size: int = 0) -> FileStorageResult:
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
        is_valid, error_msg = FileConfig.validate_report_total_size(current_report_size, file_size)
        if not is_valid:
            raise ValueError(error_msg)

        # 5. Calcular SHA-256 hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # 6. Generar nombre de archivo seguro (usar hash para evitar colisiones)
        extension = FileConfig.get_file_extension(mime_type)
        safe_filename = f"{file_hash[:16]}.{extension}"

        # 7. Ruta relativa (por fecha y reporte) y guardado vía backend
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        relative_path = str(Path(date_str) / report_id / safe_filename)
        self.backend.save(relative_path, file_content)

        return FileStorageResult(
            file_path=relative_path,
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            original_filename=file.filename or "unknown",
            file_type=mime_type,
        )

    def get_file_path(self, relative_path: str) -> Path:
        """Obtiene la ruta completa de un archivo."""
        return self.backend.resolve(relative_path)

    def delete_file(self, relative_path: str) -> bool:
        """Elimina un archivo del almacenamiento."""
        try:
            return self.backend.delete(relative_path)
        except Exception as e:
            raise ValueError(f"Error al eliminar archivo: {str(e)}")
