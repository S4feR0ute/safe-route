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
