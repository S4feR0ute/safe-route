from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

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

app = FastAPI(
    title="SafeRoute API",
    description="API de ruteo seguro para peatones. Calcula rutas minimizando el riesgo de criminalidad.",
    version="1.0.0",
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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": str(error.get("loc", [])),
            "message": str(error.get("msg", ""))
        })
    return JSONResponse(
        status_code=422,
        content={"error": {
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados no tienen el formato correcto.",
            "details": {"errors": errors},
        }},
    )

# --- Registrar routers ---
app.include_router(route_router)
app.include_router(geocode_router)
app.include_router(auth_router)
app.include_router(report_router)
app.include_router(moderation_router)


# --- Health check endpoint (sin autenticación) ---
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Endpoint de salud sin autenticación."""
    return {"status": "ok", "version": "1.0.0"}
