from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.factory import RepositoryFactory
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import DuplicateEmailError, AccountLockedError, InvalidCredentialsError
from app.db.transactions import transactional, transaction_no_close


class AuthService:
    def __init__(self, db: Session, user_repo: UserRepository = None):
        self.db = db
        self.user_repo = user_repo or RepositoryFactory.create_user_repository(db)

    @transactional
    def register(self, email: str, password: str, full_name: str = None) -> tuple[User, str]:
        """Registra un nuevo usuario y retorna (usuario, token)."""
        if self.user_repo.email_exists(email):
            raise DuplicateEmailError(f"El email {email} ya está registrado")

        user = self.user_repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name
        )
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
            with transaction_no_close(self.db):
                self.user_repo.increment_failed_login(user.id)
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        with transaction_no_close(self.db):
            self.user_repo.reset_login_attempts(user.id)

        token = create_access_token({"sub": user.email, "id": user.id})
        return user, token
