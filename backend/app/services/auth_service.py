from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.interfaces.user_interface import IUserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import DuplicateEmailError, AccountLockedError, InvalidCredentialsError


class AuthService:
    def __init__(self, db: Session, user_repo: IUserRepository = None):
        self.db = db
        if user_repo is None:
            from app.repositories.user_repository import UserRepository
            user_repo = UserRepository(db)
        self.user_repo = user_repo

    def register(self, email: str, password: str, full_name: str = None) -> tuple[User, str]:
        """Registra un nuevo usuario y retorna (usuario, token)."""
        if self.user_repo.email_exists(email):
            raise DuplicateEmailError(f"El email {email} ya está registrado")

        password_hash = hash_password(password)
        user = self.user_repo.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name
        )
        self.db.commit()

        token = create_access_token({"sub": user.email, "id": user.id})
        return user, token

    def login(self, email: str, password: str) -> tuple[User, str]:
        """Autentica un usuario y retorna (usuario, token)."""
        user = self.user_repo.get_active_user_by_email(email)

        if not user:
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        if user.locked_until and user.locked_until > datetime.utcnow():
            raise AccountLockedError("Cuenta bloqueada por demasiados intentos fallidos")

        if not verify_password(password, user.password_hash):
            self.user_repo.increment_failed_login(user.id)
            self.db.commit()
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        self.user_repo.reset_login_attempts(user.id)
        self.db.commit()

        token = create_access_token({"sub": user.email, "id": user.id})
        return user, token
