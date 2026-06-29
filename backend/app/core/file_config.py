from pathlib import Path
from typing import List

class FileConfig:
    """Configuración de almacenamiento de archivos."""

    # Tipos MIME permitidos
    ALLOWED_MIME_TYPES = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "video/mp4": "mp4",
    }

    # Extensiones de archivo permitidas
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "mp4"}

    # Tamaño máximo por archivo (10MB)
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    # Tamaño máximo total por reporte (50MB)
    MAX_REPORT_SIZE_BYTES = 50 * 1024 * 1024

    # Directorio base de uploads
    UPLOAD_BASE_DIR = Path("backend/uploads")

    # Crear directorio si no existe
    UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_mime_type_allowed(cls, mime_type: str) -> bool:
        """Verifica si el MIME type es permitido."""
        return mime_type in cls.ALLOWED_MIME_TYPES

    @classmethod
    def get_file_extension(cls, mime_type: str) -> str:
        """Obtiene la extensión del archivo según MIME type."""
        return cls.ALLOWED_MIME_TYPES.get(mime_type, "unknown")

    @classmethod
    def validate_file_size(cls, file_size_bytes: int) -> tuple[bool, str]:
        """Valida el tamaño de un archivo"""
        if file_size_bytes > cls.MAX_FILE_SIZE_BYTES:
            max_mb = cls.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return False, f"Archivo supera límite de {max_mb}MB"
        return True, ""

    @classmethod
    def validate_report_total_size(cls, current_size_bytes: int, new_file_size_bytes: int) -> tuple[bool, str]:
        """Valida si agregar un archivo supera el límite del reporte"""
        total = current_size_bytes + new_file_size_bytes
        if total > cls.MAX_REPORT_SIZE_BYTES:
            max_mb = cls.MAX_REPORT_SIZE_BYTES / (1024 * 1024)
            return False, f"Reporte superaría límite de {max_mb}MB"
        return True, ""

    @classmethod
    def get_upload_dir_for_report(cls, report_id: str) -> Path:
        """Obtiene el directorio de upload para un reporte específico."""
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        upload_dir = cls.UPLOAD_BASE_DIR / date_str / report_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
