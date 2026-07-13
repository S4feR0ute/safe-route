"""Configuración de geocodificación con Nominatim (OpenStreetMap)."""

# Bounding box completo de Lima Metropolitana + Callao
# Formato Nominatim: oeste,norte,este,sur
LIMA_VIEWBOX = "-77.20,-11.57,-76.62,-12.52"

# URL base de Nominatim
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim requiere identificar quién hace las peticiones
HEADERS = {
    "User-Agent": "SafeRoute/1.0 (proyecto universitario; contacto: saferoute@example.com)",
}

# Máximo de resultados a pedir a Nominatim
MAX_RESULTS = 5
