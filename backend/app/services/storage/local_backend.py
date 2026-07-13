from pathlib import Path

from app.core.file_config import FileConfig
from app.services.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Almacenamiento en el sistema de archivos local, bajo un directorio base."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = Path(base_dir) if base_dir else FileConfig.UPLOAD_BASE_DIR

    def resolve(self, relative_path: str) -> Path:
        return self.base_dir / relative_path

    def save(self, relative_path: str, content: bytes) -> None:
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def delete(self, relative_path: str) -> bool:
        path = self.resolve(relative_path)
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        return self.resolve(relative_path).exists()
