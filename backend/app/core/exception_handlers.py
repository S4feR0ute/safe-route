import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import AppException, error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los handlers de excepción en la app FastAPI."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        # Cada excepción de dominio ya lleva su code/status/message.
        return error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, exc: PermissionError):
        return error_response(
            code="AUTHORIZATION_DENIED",
            message=str(exc) or "No tienes permisos para acceder a este recurso",
            status_code=403,
        )

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError):
        # Errores de validación de negocio que los servicios expresan como ValueError.
        return error_response(
            code="VALIDATION_ERROR",
            message=str(exc),
            status_code=400,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {
                "field": str(error.get("loc", [])),
                "message": str(error.get("msg", "")),
            }
            for error in exc.errors()
        ]
        return error_response(
            code="VALIDATION_ERROR",
            message="Los datos enviados no tienen el formato correcto.",
            status_code=422,
            details={"errors": errors},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception(f"Unhandled error: {type(exc).__name__}")
        return error_response(
            code="INTERNAL_ERROR",
            message="Ocurrió un error interno",
            status_code=500,
        )
