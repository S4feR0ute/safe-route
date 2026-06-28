from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.route_endpoint import router as route_router
from app.api.geocode_endpoint import router as geocode_router

app = FastAPI(
    title="SafeRoute API",
    description="API de ruteo seguro para peatones. Calcula rutas minimizando el riesgo de criminalidad.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción cambiar a la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados no tienen el formato correcto.",
            "details": exc.errors(),
        }},
    )

# --- Registrar routers ---
app.include_router(route_router)
app.include_router(geocode_router)


# --- Health check endpoint (sin autenticación) ---
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Endpoint de salud sin autenticación."""
    return {"status": "ok", "version": "1.0.0"}
