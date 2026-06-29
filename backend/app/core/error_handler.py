"""
Centralizado error handling para toda la API.
Proporciona métodos estándares para diferentes tipos de errores.
"""
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse
from app.core.exceptions import error_response


class ErrorHandler:
    """Maneja errores de manera centralizada y consistente."""

    @staticmethod
    def validation_error(
        message: str,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ) -> JSONResponse:
        """Error de validación de entrada."""
        error_details = details or {}
        if field:
            error_details["field"] = field
        return error_response(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=error_details
        )

    @staticmethod
    def authentication_error(
        message: str = "Autenticación requerida",
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Error de autenticación."""
        return error_response(
            code="AUTHENTICATION_REQUIRED",
            message=message,
            status_code=401,
            details=details
        )

    @staticmethod
    def authorization_error(
        message: str = "No tienes permisos para acceder a este recurso",
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Error de autorización."""
        return error_response(
            code="AUTHORIZATION_DENIED",
            message=message,
            status_code=403,
            details=details
        )

    @staticmethod
    def not_found(
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Recurso no encontrado."""
        return error_response(
            code="NOT_FOUND",
            message=f"{resource} no encontrado",
            status_code=404,
            details=details
        )

    @staticmethod
    def conflict_error(
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Error de conflicto (ej: duplicado)."""
        return error_response(
            code="CONFLICT",
            message=message,
            status_code=409,
            details=details
        )

    @staticmethod
    def business_error(
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Error de lógica de negocio genérico."""
        return error_response(
            code=code,
            message=message,
            status_code=status_code,
            details=details
        )

    @staticmethod
    def internal_error(
        message: str = "Ocurrió un error interno",
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Error interno del servidor."""
        return error_response(
            code="INTERNAL_ERROR",
            message=message,
            status_code=500,
            details=details
        )

    @staticmethod
    def service_unavailable(
        message: str = "Servicio no disponible",
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Servicio no disponible."""
        return error_response(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=503,
            details=details
        )
