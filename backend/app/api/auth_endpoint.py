from fastapi import APIRouter, Depends, status
import logging

from app.schemas.auth_schemas import UserRegisterRequest, UserLoginRequest, AuthTokenResponse
from app.core.service_container import ServiceContainer, get_service_container
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Registra un nuevo usuario ciudadano.
    Retorna token JWT para usar en endpoints protegidos.
    """
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
    except ValueError as e:
        msg = str(e)
        if "ya está registrado" in msg:
            return ErrorHandler.conflict_error(
                message="El email ya está registrado",
                details={"email": request.email}
            )
        return ErrorHandler.validation_error(message=str(e), field="register")
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
    """
    Autentica un usuario y retorna token JWT.
    El token se envía en el header: `Authorization: Bearer <token>`
    """
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
    except ValueError as e:
        msg = str(e)
        if "bloqueada" in msg:
            return ErrorHandler.business_error(
                code="ACCOUNT_LOCKED",
                message="Cuenta bloqueada por demasiados intentos fallidos",
                status_code=423
            )
        if "Email o contraseña" in msg:
            return ErrorHandler.authentication_error(
                message="Email o contraseña incorrectos"
            )
        return ErrorHandler.validation_error(message=str(e), field="login")
    except Exception as e:
        logger.exception(f"Login error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Ocurrió un error al autenticar"
        )
