from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, email: str, password: str, full_name: str = None) -> tuple[User, str]:
        """
        Registra un nuevo usuario y retorna (usuario, token).
        Lanza ValueError si el email ya existe.
        """
        if self.user_repo.email_exists(email):
            raise ValueError(f"El email {email} ya está registrado")

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
        """
        Autentica un usuario y retorna (usuario, token).
        Lanza ValueError si las credenciales son inválidas o la cuenta está bloqueada.
        """
        user = self.user_repo.get_active_user_by_email(email)

        if not user:
            raise ValueError("Email o contraseña incorrectos")

        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError("Cuenta bloqueada por demasiados intentos fallidos")

        if not verify_password(password, user.password_hash):
            self.user_repo.increment_failed_login(user.id)
            self.db.commit()
            raise ValueError("Email o contraseña incorrectos")

        self.user_repo.reset_login_attempts(user.id)
        self.db.commit()

        token = create_access_token({"sub": user.email, "id": user.id})
        return user, token
