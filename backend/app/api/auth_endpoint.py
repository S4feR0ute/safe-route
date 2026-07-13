from fastapi import APIRouter, Depends, status

from app.schemas.auth_schemas import UserRegisterRequest, UserLoginRequest, AuthTokenResponse
from app.core.service_container import ServiceContainer, get_service_container

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """Registra un nuevo usuario ciudadano."""
    user, token = container.get_auth_service().register(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )
    return AuthTokenResponse(access_token=token, token_type="bearer", user=user)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: UserLoginRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """Autentica un usuario y retorna token JWT."""
    user, token = container.get_auth_service().login(
        email=request.email,
        password=request.password,
    )
    return AuthTokenResponse(access_token=token, token_type="bearer", user=user)
