from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def save(self, relative_path: str, content: bytes) -> None:
        """Guarda `content` en la ubicación identificada por `relative_path`."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Elimina el archivo. Devuelve True si existía y se eliminó."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Indica si el archivo existe."""
        raise NotImplementedError

    @abstractmethod
    def resolve(self, relative_path: str) -> Path:
        """Devuelve la ruta absoluta correspondiente al `relative_path`."""
        raise NotImplementedError
