"""Constantes del dominio de reportes ciudadanos (tipos, modos, estados, límites)."""

# Tipos de incidencia válidos
INCIDENT_TYPES = {
    "robo",
    "asalto",
    "violencia",
    "droga",
    "acoso",
    "vandalismo",
    "venta_ambulante",
    "ocupacion_via",
    "otro",
}

# Modos de reporte
REPORT_MODE_ANONYMOUS = 1       # Sin cuenta, sin documentos
REPORT_MODE_AUTHENTICATED = 2   # Con cuenta, sin documentos
REPORT_MODE_DOCUMENTED = 3      # Con cuenta + documentos sustentatorios

# Estados de reporte
REPORT_STATUS_PENDING = "pending"
REPORT_STATUS_VALIDATED = "validated"
REPORT_STATUS_REJECTED = "rejected"

# Radio de búsqueda para reportes cercanos (metros)
REPORT_SEARCH_RADIUS_M = 500

# Límites de file upload (modo 3)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_TYPES = {"pdf", "jpg", "jpeg", "png"}

# Rate limiting
REPORTS_PER_USER_PER_DAY = 10  # Máximo reportes/usuario/día
REPORTS_PER_IP_PER_HOUR = 5    # Máximo reportes/IP/hora (modo 1)
