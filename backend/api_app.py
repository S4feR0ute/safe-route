import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import API_TITLE, API_DESCRIPTION, API_VERSION
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import ServiceUnavailableError
from app.db.session import get_db
from app.api.route_endpoint import router as route_router
from app.api.geocode_endpoint import router as geocode_router
from app.api.auth_endpoint import router as auth_router
from app.api.report_endpoints import router as report_router
from app.api.moderation_endpoints import router as moderation_router
from app.middleware.security_middleware import (
    SecurityHeadersMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción cambiar a la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Manejo centralizado de errores ---
register_exception_handlers(app)

# --- Registrar routers ---
app.include_router(route_router)
app.include_router(geocode_router)
app.include_router(auth_router)
app.include_router(report_router)
app.include_router(moderation_router)


# --- Health check endpoint (sin autenticación) ---
@app.get("/api/v1/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Endpoint de salud: verifica el servicio y la conexión a la BD."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise ServiceUnavailableError(message="La base de datos no está disponible")
    return {"status": "ok", "database": "ok", "version": API_VERSION}
