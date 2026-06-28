"""
Validadores personalizados para prevenir inyección SQL y parámetros malformados.
Sprint 3 - Seguridad (OWASP Top 10)
"""
import re
from typing import Any
from pydantic import field_validator, ValidationInfo
from email_validator import validate_email, EmailNotValidError


class SQLInjectionValidator:
    """
    Detecta patrones comunes de inyección SQL.
    Nota: SQLAlchemy usa parámetros preparados por defecto, pero esta validación
    proporciona defensa en profundidad.
    """

    # Patrones SQL peligrosos
    SQL_PATTERNS = [
        r"(\bOR\b|AND\b).*=.*",  # OR/AND logic
        r"(;|--|\*|\/\*|\*\/)",  # SQL comments/terminators
        r"(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)",
        r"(xp_|sp_)",  # SQL Server stored procedures
    ]

    SQL_REGEX = re.compile("|".join(SQL_PATTERNS), re.IGNORECASE)

    @staticmethod
    def is_safe(value: str) -> bool:
        """Verifica si un string es seguro contra SQL injection."""
        if not isinstance(value, str):
            return True
        return not SQLInjectionValidator.SQL_REGEX.search(value)

    @staticmethod
    def validate(value: str, field_name: str = "field") -> str:
        """Valida un string contra SQL injection. Lanza ValueError si es inseguro."""
        if not SQLInjectionValidator.is_safe(value):
            raise ValueError(f"{field_name} contiene caracteres no permitidos")
        return value


class InputValidator:
    """Validadores comunes para inputs de usuario."""

    @staticmethod
    def validate_email(email: str) -> str:
        """Valida email contra formato y inyección SQL."""
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            raise ValueError(f"Email inválido: {str(e)}")

        # Validar contra SQL injection
        SQLInjectionValidator.validate(email, "email")
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Valida contraseña:
        - Mínimo 8 caracteres
        - Al menos una mayúscula, una minúscula, un número
        """
        if len(password) < 8:
            raise ValueError("Contraseña debe tener al menos 8 caracteres")
        if len(password) > 255:
            raise ValueError("Contraseña muy larga (máximo 255 caracteres)")

        if not re.search(r"[a-z]", password):
            raise ValueError("Contraseña debe contener minúsculas")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Contraseña debe contener mayúsculas")
        if not re.search(r"[0-9]", password):
            raise ValueError("Contraseña debe contener números")

        return password

    @staticmethod
    def validate_string(value: str, field_name: str = "field", max_length: int = 255) -> str:
        """
        Valida string genérico:
        - No contiene SQL injection
        - Longitud máxima
        - Sin caracteres de control peligrosos
        """
        if not isinstance(value, str):
            raise ValueError(f"{field_name} debe ser string")

        if len(value) == 0:
            raise ValueError(f"{field_name} no puede estar vacío")

        if len(value) > max_length:
            raise ValueError(f"{field_name} no puede exceder {max_length} caracteres")

        # Validar contra SQL injection
        SQLInjectionValidator.validate(value, field_name)

        # Validar sin caracteres de control peligrosos
        if re.search(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", value):
            raise ValueError(f"{field_name} contiene caracteres de control no permitidos")

        return value.strip()

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
        """
        Valida coordenadas geográficas (Lima Metropolitana).
        - Latitud: -12.3 a -11.8
        - Longitud: -77.2 a -76.8
        """
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            raise ValueError("Coordenadas deben ser números")

        # Validar rango de Lima
        if not (-12.3 <= lat <= -11.8):
            raise ValueError("Latitud fuera de rango de Lima Metropolitana (-12.3 a -11.8)")
        if not (-77.2 <= lon <= -76.8):
            raise ValueError("Longitud fuera de rango de Lima Metropolitana (-77.2 a -76.8)")

        return lat, lon

    @staticmethod
    def validate_integer(value: Any, field_name: str = "field", min_val: int = None, max_val: int = None) -> int:
        """Valida que sea entero dentro de rango."""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} debe ser un número entero")

        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} no puede ser menor que {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} no puede ser mayor que {max_val}")

        return value


class SchemaValidators:
    """
    Validadores Pydantic reutilizables.
    Se usan con @field_validator en Pydantic models.
    """

    @staticmethod
    def validate_email_field(value: str) -> str:
        """Para usar en Pydantic: @field_validator('email')"""
        return InputValidator.validate_email(value)

    @staticmethod
    def validate_password_field(value: str) -> str:
        """Para usar en Pydantic: @field_validator('password')"""
        return InputValidator.validate_password(value)

    @staticmethod
    def validate_string_field(value: str, max_length: int = 255) -> str:
        """Para usar en Pydantic: @field_validator('name')"""
        return InputValidator.validate_string(value, max_length=max_length)
