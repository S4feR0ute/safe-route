from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.core.security import verify_token, extract_token_from_header

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """
    Dependencia para extraer y validar JWT del header Authorization.
    Retorna el payload del token decodificado.
    """
    token = credentials.credentials
    payload = verify_token(token)
    return payload


async def get_current_user_optional(credentials: HTTPAuthCredentials = None) -> dict | None:
    """
    Dependencia opcional: valida JWT si está presente, pero no falla si no lo está.
    """
    if not credentials:
        return None

    token = credentials.credentials
    try:
        payload = verify_token(token)
        return payload
    except HTTPException:
        return None
