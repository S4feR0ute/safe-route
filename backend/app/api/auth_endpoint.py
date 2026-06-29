from fastapi import APIRouter, Depends, status
import logging

from app.schemas.auth_schemas import UserRegisterRequest, UserLoginRequest, AuthTokenResponse
from app.core.service_container import ServiceContainer, get_service_container
from app.core.error_handler import ErrorHandler
from app.core.exceptions import DuplicateEmailError, AccountLockedError, InvalidCredentialsError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """Registra un nuevo usuario ciudadano."""
    try:
        auth_service = container.get_auth_service()
        user, token = auth_service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=user
        )
    except DuplicateEmailError:
        return ErrorHandler.conflict_error(
            message="El email ya está registrado",
            details={"email": request.email}
        )
    except Exception as e:
        logger.exception(f"Registration error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Ocurrió un error al registrar el usuario"
        )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: UserLoginRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """Autentica un usuario y retorna token JWT."""
    try:
        auth_service = container.get_auth_service()
        user, token = auth_service.login(
            email=request.email,
            password=request.password
        )
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=user
        )
    except AccountLockedError:
        return ErrorHandler.business_error(
            code="ACCOUNT_LOCKED",
            message="Cuenta bloqueada por demasiados intentos fallidos",
            status_code=423
        )
    except InvalidCredentialsError:
        return ErrorHandler.authentication_error(
            message="Email o contraseña incorrectos"
        )
    except Exception as e:
        logger.exception(f"Login error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Ocurrió un error al autenticar"
        )
