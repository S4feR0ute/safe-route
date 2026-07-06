import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# JWT Configuration
_DEFAULT_JWT_SECRET = "trabajo_final_safe_route_2026"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEFAULT_JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", 30)))

if JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
    if ENVIRONMENT != "development":
        raise RuntimeError(
            "JWT_SECRET_KEY no configurado: define la variable de entorno "
            "JWT_SECRET_KEY antes de correr fuera de desarrollo."
        )
    logger.warning(
        "JWT_SECRET_KEY usa el valor por defecto (solo aceptable en desarrollo)."
    )

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "SafeRoute API"
API_DESCRIPTION = "API de ruteo seguro para peatones. Calcula rutas minimizando el riesgo de criminalidad."

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL_LOCAL")

# Fuente de datos SIDPOL (Excel del observatorio MININTER)
SIDPOL_SOURCE_URL = os.getenv(
    "SIDPOL_SOURCE_URL",
    "https://observatorio.mininter.gob.pe/sites/default/files/proyecto/archivos/Base_datos_SIDPOL_Marzo2026.xlsx",
)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
