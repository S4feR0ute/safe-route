from typing import Optional
from fastapi.responses import JSONResponse


class AppException(Exception):
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "Ocurrió un error interno"

    def __init__(self, message: Optional[str] = None, details: Optional[dict] = None):
        self.message = message or type(self).message
        self.details = details or {}
        super().__init__(self.message)


# --- Validación genérica ---
class ValidationError(AppException):
    code = "VALIDATION_ERROR"
    status_code = 400
    message = "Los datos enviados no son válidos"


# --- Autenticación / Autorización ---
class AuthenticationRequired(AppException):
    code = "AUTHENTICATION_REQUIRED"
    status_code = 401
    message = "Autenticación requerida"


class AuthorizationDenied(AppException):
    code = "AUTHORIZATION_DENIED"
    status_code = 403
    message = "No tienes permisos para acceder a este recurso"


# --- Servicio no disponible ---
class ServiceUnavailableError(AppException):
    code = "SERVICE_UNAVAILABLE"
    status_code = 503
    message = "Servicio no disponible"


# --- Routing ---
class EmptyGraphError(AppException):
    code = "SERVICE_UNAVAILABLE"
    status_code = 503
    message = "Los datos de rutas no han sido inicializados"


class NoRouteError(AppException):
    code = "NOT_FOUND"
    status_code = 404
    message = "No existe una ruta peatonal disponible"


class NodeNotFoundError(AppException):
    code = "NOT_FOUND"
    status_code = 404
    message = "No existe una ruta peatonal disponible"


# --- Autenticación (dominio de usuarios) ---
class DuplicateEmailError(AppException):
    code = "CONFLICT"
    status_code = 409
    message = "El email ya está registrado"


class AccountLockedError(AppException):
    code = "ACCOUNT_LOCKED"
    status_code = 423
    message = "Cuenta bloqueada por demasiados intentos fallidos"


class InvalidCredentialsError(AppException):
    code = "AUTHENTICATION_REQUIRED"
    status_code = 401
    message = "Email o contraseña incorrectos"


# --- Reportes ---
class ReportNotFoundError(AppException):
    code = "NOT_FOUND"
    status_code = 404
    message = "Reporte no encontrado"


class InvalidReportStateError(AppException):
    code = "VALIDATION_ERROR"
    status_code = 400
    message = "El reporte no está en el estado requerido para la operación"


class DuplicateFileError(AppException):
    code = "CONFLICT"
    status_code = 409
    message = "Ya existe un documento con el mismo contenido (hash SHA-256)"


def error_response(code: str, message: str, status_code: int, details: Optional[dict] = None) -> JSONResponse:
    """Factory para crear respuestas de error consistentes (sobre {"error": {...}})."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {
            "code": code,
            "message": message,
            "details": details or {}
        }}
    )
