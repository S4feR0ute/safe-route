from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import hashlib
import secrets
from fastapi import HTTPException, status
from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION


def hash_password(password: str) -> str:
    """Hash de contraseña con PBKDF2-SHA256."""
    password = password[:72].encode('utf-8')
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password, salt.encode(), 100000)
    return f"{salt}${hash_obj.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra su hash."""
    try:
        plain_password = plain_password[:72].encode('utf-8')
        salt, hash_hex = hashed_password.split('$')
        hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password, salt.encode(), 100000)
        return hash_obj.hex() == hash_hex
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT con los datos proporcionados."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + JWT_EXPIRATION

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verifica y decodifica un JWT. Lanza excepción si es inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_token_from_header(authorization: str) -> str:
    """Extrae el token del header Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ")[1]
