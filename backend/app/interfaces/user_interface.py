from abc import ABC, abstractmethod
from typing import Optional, List
class IUserRepository(ABC):
    """Interfaz para repositories de usuarios."""

    @abstractmethod
    def get_by_email(self, email: str):
        """Obtiene usuario por email."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int):
        """Obtiene usuario por ID."""
        pass

    @abstractmethod
    def get_active_user_by_email(self, email: str):
        """Obtiene usuario activo y no eliminado por email (para login)."""
        pass

    @abstractmethod
    def create(self, email: str, password_hash: str, full_name: Optional[str] = None, phone_number: Optional[str] = None):
        """Crea un nuevo usuario (tipo 'citizen' por defecto)."""
        pass

    @abstractmethod
    def email_exists(self, email: str) -> bool:
        """Verifica si el email ya existe."""
        pass

    @abstractmethod
    def get_active_users(self, limit: int = 100) -> List:
        """Obtiene usuarios activos (no eliminados)."""
        pass

    @abstractmethod
    def get_verified_moderators(self, limit: int = 100) -> List:
        """Obtiene moderadores verificados."""
        pass

    @abstractmethod
    def promote_to_moderator(self, user_id: int, moderator_role: str = "moderator"):
        """Promueve un usuario a moderador."""
        pass

    @abstractmethod
    def verify_moderator(self, user_id: int):
        """Verifica un moderador después de proceso de validación."""
        pass

    @abstractmethod
    def deactivate(self, user_id: int) -> bool:
        """Desactiva un usuario (soft delete)."""
        pass

    @abstractmethod
    def reset_login_attempts(self, user_id: int):
        """Resetea intentos fallidos después de login exitoso."""
        pass

    @abstractmethod
    def increment_failed_login(self, user_id: int, max_attempts: int = 5) -> bool:
        """Incrementa intentos fallidos de login y bloquea si es necesario."""
        pass
