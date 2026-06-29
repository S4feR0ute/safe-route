from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verify_token, extract_token_from_header
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
        user = user_repo.get_by_id(int(user_id))
        return user

    except Exception:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Extrae usuario del token JWT y lo retorna.
    Lanza excepción HTTPException si no hay token o es inválido.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = extract_token_from_header(authorization)
        payload = verify_token(token)
        user_id = payload.get("id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        user_repo = container.get_user_repository()
        user = user_repo.get_by_id(int(user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


async def get_moderator(
    current_user = Depends(get_current_user),
):
    """
    Valida que el usuario actual sea moderador.
    Lanza excepción HTTPException si no tiene permisos.
    """
    if current_user.user_type != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Solo moderadores pueden acceder a este recurso",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de moderador desactivada",
        )

    return current_user


async def get_admin(
    current_user = Depends(get_current_user),
):
    """
    Valida que el usuario actual sea admin.
    Lanza excepción HTTPException si no tiene permisos.
    """
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Solo administradores pueden acceder a este recurso",
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de administrador desactivada",
        )

    return current_user
