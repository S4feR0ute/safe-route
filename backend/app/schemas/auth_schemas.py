from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.core.validators import InputValidator


class UserRegisterRequest(BaseModel):
    """Request para registrar nuevo usuario."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return InputValidator.validate_email(v)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return InputValidator.validate_password(v)

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return InputValidator.validate_string(v, "full_name", max_length=255)


class UserLoginRequest(BaseModel):
    """Request para login."""
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return InputValidator.validate_email(v)


class UserResponse(BaseModel):
    """Response de usuario (sin password)."""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthTokenResponse(BaseModel):
    """Response de login/register con token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthErrorResponse(BaseModel):
    """Response de error de auth."""
    error: dict = Field(..., description="Error details")

    class Config:
        example = {
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Email o contraseña incorrectos",
                "details": {}
            }
        }
