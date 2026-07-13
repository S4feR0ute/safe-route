import re
from typing import Any
from email_validator import validate_email, EmailNotValidError


class SQLInjectionValidator:

    SQL_PATTERNS = [
        r"(\bOR\b|AND\b).*=.*",  # OR/AND logic
        r"(;|--|\*|\/\*|\*\/)",  # SQL comments/terminators
        r"(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)",
        r"(xp_|sp_)",  # SQL Server stored procedures
    ]

    _regex = re.compile("|".join(SQL_PATTERNS), re.IGNORECASE)

    @staticmethod
    def is_safe(value: str) -> bool:
        """True si el valor no contiene patrones SQL peligrosos."""
        if not isinstance(value, str):
            return True
        return not SQLInjectionValidator._regex.search(value)

    @staticmethod
    def validate(value: str, field_name: str = "field") -> str:
        """Lanza ValueError si encuentra patrones SQL peligrosos."""
        if not SQLInjectionValidator.is_safe(value):
            raise ValueError(f"{field_name} contiene caracteres no permitidos")
        return value


class EmailValidator:
    """Única responsabilidad: Validar emails."""

    @staticmethod
    def validate(email: str) -> str:
        """Valida formato y previene SQL injection."""
        if not email or not isinstance(email, str):
            raise ValueError("Email debe ser un string")

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            raise ValueError(f"Email inválido: {str(e)}")

        SQLInjectionValidator.validate(email, "email")
        return email


class PasswordValidator:
    """Única responsabilidad: Validar contraseñas."""

    MIN_LENGTH = 8
    MAX_LENGTH = 72  # Límite de bcrypt

    @staticmethod
    def validate(password: str) -> str:
        """Valida: longitud, mayúscula, minúscula, números."""
        if len(password) < PasswordValidator.MIN_LENGTH:
            raise ValueError(f"Mínimo {PasswordValidator.MIN_LENGTH} caracteres")
        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError(f"Máximo {PasswordValidator.MAX_LENGTH} caracteres (límite de bcrypt)")

        if not re.search(r"[a-z]", password):
            raise ValueError("Debe contener minúsculas")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Debe contener mayúsculas")
        if not re.search(r"[0-9]", password):
            raise ValueError("Debe contener números")

        return password


class StringValidator:
    """Única responsabilidad: Validar strings genéricos."""
    
    DANGEROUS_CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

    @staticmethod
    def validate(value: str, field_name: str = "field", max_length: int = 255) -> str:
        """Valida: tipo, no vacío, longitud, SQL injection, control chars."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} debe ser string")

        if not value.strip():
            raise ValueError(f"{field_name} no puede estar vacío")

        if len(value) > max_length:
            raise ValueError(f"{field_name} máximo {max_length} caracteres")

        SQLInjectionValidator.validate(value, field_name)

        if StringValidator.DANGEROUS_CONTROL_PATTERN.search(value):
            raise ValueError(f"{field_name} contiene caracteres de control peligrosos")

        return value.strip()


class CoordinateValidator:
    """Única responsabilidad: Validar coordenadas geográficas."""

    # Límites de Lima Metropolitana
    LAT_MIN, LAT_MAX = -12.3, -11.8
    LON_MIN, LON_MAX = -77.2, -76.8

    @staticmethod
    def validate(lat: float, lon: float) -> tuple[float, float]:
        """Valida coordenadas dentro de Lima Metropolitana."""
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            raise ValueError("Coordenadas deben ser números")

        if not (CoordinateValidator.LAT_MIN <= lat <= CoordinateValidator.LAT_MAX):
            raise ValueError(
                f"Latitud fuera de rango "
                f"({CoordinateValidator.LAT_MIN} a {CoordinateValidator.LAT_MAX})"
            )
        if not (CoordinateValidator.LON_MIN <= lon <= CoordinateValidator.LON_MAX):
            raise ValueError(
                f"Longitud fuera de rango "
                f"({CoordinateValidator.LON_MIN} a {CoordinateValidator.LON_MAX})"
            )

        return lat, lon


class IntegerValidator:
    """Única responsabilidad: Validar enteros."""

    @staticmethod
    def validate(
        value: Any,
        field_name: str = "field",
        min_val: int = None,
        max_val: int = None
    ) -> int:
        """Valida tipo y rango."""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} debe ser número entero")

        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} mínimo: {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} máximo: {max_val}")

        return value


class InputValidator:
    """Interfaz de compatibilidad que delega a validadores específicos."""

    @staticmethod
    def validate_email(email: str) -> str:
        return EmailValidator.validate(email)

    @staticmethod
    def validate_password(password: str) -> str:
        return PasswordValidator.validate(password)

    @staticmethod
    def validate_string(value: str, field_name: str = "field", max_length: int = 255) -> str:
        return StringValidator.validate(value, field_name, max_length)

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
        return CoordinateValidator.validate(lat, lon)

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str = "field",
        min_val: int = None,
        max_val: int = None
    ) -> int:
        return IntegerValidator.validate(value, field_name, min_val, max_val)
