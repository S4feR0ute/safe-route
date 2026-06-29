from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.interfaces.user_interface import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """Obtiene usuario por email (incluyendo eliminados)."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene usuario por ID (incluyendo eliminados)."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_active_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene usuario activo y no eliminado por email (para login)."""
        return self.db.query(User).filter(
            User.email == email,
            User.is_active == True,
            User.deleted_at == None
        ).first()

    def create(self, email: str, password_hash: str, full_name: Optional[str] = None, phone_number: Optional[str] = None) -> User:
        """Crea un nuevo usuario (tipo 'citizen' por defecto)."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone_number=phone_number,
            user_type="citizen",
        )
        self.db.add(user)
        self.db.flush()
        return user

    def email_exists(self, email: str) -> bool:
        """Verifica si el email ya existe (incluyendo eliminados)."""
        return self.db.query(User).filter(User.email == email).first() is not None

    def get_active_users(self, limit: int = 100) -> List[User]:
        """Obtiene usuarios activos (no eliminados)."""
        return self.db.query(User).filter(
            User.is_active == True,
            User.deleted_at == None
        ).limit(limit).all()

    def get_verified_moderators(self, limit: int = 100) -> List[User]:
        """Obtiene moderadores verificados."""
        return self.db.query(User).filter(
            User.user_type.in_(["moderator", "admin"]),
            User.is_verified_moderator == True,
            User.is_active == True,
            User.deleted_at == None
        ).limit(limit).all()

    def promote_to_moderator(self, user_id: int, moderator_role: str = "moderator") -> Optional[User]:
        """Promueve un usuario a moderador."""
        user = self.get_by_id(user_id)
        if user and user.user_type == "citizen":
            user.user_type = "moderator"
            user.moderator_role = moderator_role
            user.moderator_since = datetime.utcnow()
            return user
        return None

    def verify_moderator(self, user_id: int) -> Optional[User]:
        """Verifica un moderador después de proceso de validación."""
        user = self.get_by_id(user_id)
        if user and user.user_type in ["moderator", "admin"]:
            user.is_verified_moderator = True
            return user
        return None

    def deactivate(self, user_id: int) -> bool:
        """Desactiva un usuario (soft delete)."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            return True
        return False

    def reset_login_attempts(self, user_id: int) -> Optional[User]:
        """Resetea intentos fallidos después de login exitoso."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            return user
        return None

    def increment_failed_login(self, user_id: int, max_attempts: int = 5) -> bool:
        """Incrementa intentos fallidos de login. Si alcanza max_attempts, bloquea la cuenta"""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            return True
        return False
