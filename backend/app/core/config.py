import os
from datetime import timedelta

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-clave-secreta-cambiar-123456789abcdef")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", 30)))

# Bcrypt Configuration
BCRYPT_ROUNDS = 12

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
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/safe_route"
)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
