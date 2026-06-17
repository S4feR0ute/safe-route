from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.route_endpoint import router

app = FastAPI(
    title="SafeRoute API",
    description="API de ruteo seguro para peatones. Calcula rutas minimizando el riesgo de criminalidad.",
    version="1.0.0",
)

# --- CORS: permitir que el frontend se conecte ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción cambiar a la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Handler de errores de validación Pydantic ---
# FastAPI devuelve 422 con su propio formato; lo convertimos al formato uniforme del proyecto.
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

# --- Registrar el router con los endpoints ---
app.include_router(router)
