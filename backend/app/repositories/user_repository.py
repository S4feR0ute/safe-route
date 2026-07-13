from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Retorna un usuario por ID, incluyendo eliminados."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_active_user_by_email(self, email: str) -> Optional[User]:
        """Retorna un usuario activo por email, ignorando eliminados."""
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

    def reset_login_attempts(self, user_id: int) -> Optional[User]:
        """Resetea intentos fallidos después de login exitoso."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            return user
        return None

    def increment_failed_login(self, user_id: int, max_attempts: int = 5) -> bool:
        """Incrementa intentos fallidos y bloquea si excede max_attempts."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            return True
        return False
