from fastapi.responses import JSONResponse
from typing import Optional


class ApiException(Exception):
    """Excepción base para errores en la API."""
    def __init__(self, code: str, message: str, status_code: int, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ServiceError(Exception):
    """Excepción base para errores de servicios."""
    pass


class EmptyGraphError(ServiceError):
    """El grafo de calles está vacío."""
    pass


class NoRouteError(ServiceError):
    """No existe ruta entre los puntos especificados."""
    pass


class NodeNotFoundError(ServiceError):
    """Nodo no encontrado en el grafo."""
    pass


class DuplicateEmailError(ServiceError):
    """El email ya está registrado."""
    pass


class AccountLockedError(ServiceError):
    """Cuenta bloqueada por demasiados intentos fallidos."""
    pass


class InvalidCredentialsError(ServiceError):
    """Credenciales inválidas."""
    pass


class ReportNotFoundError(ServiceError, ValueError):
    """El reporte no existe."""
    pass


class InvalidReportStateError(ServiceError, ValueError):
    """El reporte no está en el estado requerido para la operación."""
    pass


class DuplicateFileError(ServiceError):
    """Ya existe un documento con el mismo contenido (hash SHA-256)."""
    pass


def error_response(code: str, message: str, status_code: int, details: Optional[dict] = None) -> JSONResponse:
    """Factory para crear respuestas de error consistentes."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {
            "code": code,
            "message": message,
            "details": details or {}
        }}
    )
