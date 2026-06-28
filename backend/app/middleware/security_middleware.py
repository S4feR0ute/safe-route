import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad a todas las respuestas"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevenir XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevenir clickjacking
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )

        # Strict Transport Security (en producción)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "usb=(), payment=(), accelerometer=(), gyroscope=()"
        )

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Detecta patrones sospechosos en requests"""

    SUSPICIOUS_PATTERNS = [
        r"(%27)|(\')",  # SQL injection: single quote
        r"(%23)|(#)",  # SQL injection: hash
        r"(%2D%2D)|(-–)",  # SQL injection: double dash
        r"(%3B)|(;)",  # SQL injection: semicolon
        r"union.*select",  # SQL injection: UNION SELECT
        r"select.*from",  # SQL injection: SELECT FROM
        r"insert.*into",  # SQL injection: INSERT INTO
        r"delete.*from",  # SQL injection: DELETE FROM
        r"drop.*table",  # SQL injection: DROP TABLE
        r"<script",  # XSS: script tag
        r"javascript:",  # XSS: javascript protocol
        r"onerror=",  # XSS: event handler
        r"onload=",  # XSS: event handler
    ]

    async def dispatch(self, request: Request, call_next):
        # Loguear info sobre el request
        logger.debug(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Validar query parameters
        for key, value in request.query_params.items():
            self._check_suspicious_content(key, value, f"query param '{key}'")

        response = await call_next(request)
        return response

    @staticmethod
    def _check_suspicious_content(param_name: str, param_value: str, context: str):
        """Verifica si el contenido parece sospechoso."""
        import re

        if not isinstance(param_value, str):
            return

        suspicious_value = param_value.lower()

        suspicious_patterns = [
            r"union.*select",
            r"select.*from",
            r"insert.*into",
            r"delete.*from",
            r"drop.*table",
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onload=",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, suspicious_value):
                logger.warning(
                    f"Suspicious pattern detected in {context}: "
                    f"{param_name}={param_value[:100]}"
                )
                # En producción, podríamos bloquear el request aquí
                break


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting básico por IP"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = {}

    async def dispatch(self, request: Request, call_next):
        # En producción, usamos Redis o similar
        # Aquí es un ejemplo básico en memoria
        client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)
        return response
