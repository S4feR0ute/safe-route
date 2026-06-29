from typing import Optional
from fastapi import Header, Depends
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
        user_id = payload.get("sub")

        if not user_id:
            return None

        user_repo = container.get_user_repository()
        user = user_repo.get_by_id(int(user_id))
        return user

    except Exception:
        return None
