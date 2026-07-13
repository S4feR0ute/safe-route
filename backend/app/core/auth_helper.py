from typing import Optional
from fastapi import Header, Depends

from app.core.security import verify_token, extract_token_from_header
from app.core.exceptions import AuthenticationRequired, AuthorizationDenied
from app.core.service_container import ServiceContainer, get_service_container


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Extrae usuario del token JWT si está presente.
    Si no hay token o es inválido, retorna None (no lanza excepción).
    """
    if not authorization:
        return None

    try:
        token = extract_token_from_header(authorization)
        payload = verify_token(token)
        user_id = payload.get("id")

        if not user_id:
            return None

        user_repo = container.get_user_repository()
        return user_repo.get_by_id(int(user_id))

    except Exception:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Extrae usuario del token JWT y lo retorna.
    Lanza AuthenticationRequired si no hay token o es inválido.
    """
    if not authorization:
        raise AuthenticationRequired("Token de autenticación requerido")

    try:
        token = extract_token_from_header(authorization)
        payload = verify_token(token)
        user_id = payload.get("id")
    except AuthenticationRequired:
        raise
    except Exception:
        raise AuthenticationRequired("Token inválido o expirado")

    if not user_id:
        raise AuthenticationRequired("Token inválido")

    user = container.get_user_repository().get_by_id(int(user_id))
    if not user:
        raise AuthenticationRequired("Usuario no encontrado")

    return user


async def get_moderator(
    current_user = Depends(get_current_user),
):
    """
    Valida que el usuario actual sea moderador (o admin).
    Lanza AuthorizationDenied si no tiene permisos.
    """
    if current_user.user_type not in ("moderator", "admin"):
        raise AuthorizationDenied(
            "Acceso restringido: Solo moderadores pueden acceder a este recurso"
        )

    if not current_user.is_active:
        raise AuthorizationDenied("Cuenta de moderador desactivada")

    return current_user
