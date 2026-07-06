
# Mapeo de tipos relevantes para seguridad peatonal y sus pesos 
CRIME_WEIGHTS_MAP = {
    "ROBO": 1.0,
    "HOMICIDIO": 1.0,
    "VIOLACION DE LA LIBERTAD SEXUAL": 1.0,
    "VIOLACION DE LA LIBERTAD PERSONAL": 0.9,
    "EXTORSION": 0.9,
    "TRATA DE PERSONAS": 0.9,
    "LESIONES": 0.8,
    "HURTO": 0.7,
    "PAZ PUBLICA": 0.6,
    "PELIGRO COMUN": 0.6,
    "DAÑOS": 0.5,
    "RECEPTACION": 0.4,
    "VIOLACION DE DOMICILIO": 0.4,
    "EXPOSICION A PELIGRO O ABANDONO DE PERSONAS EN PELIGRO": 0.8
}

# Distritos
TARGET_DISTRICTS = [
    # --- LIMA ---
    "Ancón, Lima, Peru",
    "Ate, Lima, Peru",
    "Barranco, Lima, Peru",
    "Breña, Lima, Peru",
    "Carabayllo, Lima, Peru",
    "Chaclacayo, Lima, Peru",
    "Chorrillos, Lima, Peru",
    "Cieneguilla, Lima, Peru",
    "Comas, Lima, Peru",
    "El Agustino, Lima, Peru",
    "Independencia, Lima, Peru",
    "Jesús María, Lima, Peru",
    "La Molina, Lima, Peru",
    "La Victoria, Lima, Peru",
    "Lima District, Lima, Peru",
    "Lince, Lima, Peru",
    "Los Olivos, Lima, Peru",
    "Lurigancho, Lima, Peru",
    "Lurín, Lima, Peru",
    "Magdalena del Mar, Lima, Peru",
    "Miraflores, Lima, Peru",
    "Pachacámac, Lima, Peru",
    "Pucusana, Lima, Peru",
    "Pueblo Libre, Lima, Peru",
    "Puente Piedra, Lima, Peru",
    "Punta Hermosa, Lima, Peru",
    "Punta Negra, Lima, Peru",
    "Rímac, Lima, Peru",
    "San Bartolo, Lima, Peru",
    "San Borja, Lima, Peru",
    "San Isidro, Lima, Peru",
    "San Juan de Lurigancho, Lima, Peru",
    "San Juan de Miraflores, Lima, Peru",
    "San Luis, Lima, Peru",
    "San Martín de Porres, Lima, Peru",
    "San Miguel, Lima, Peru",
    "Santa Anita, Lima, Peru",
    "Santa María del Mar, Lima, Peru",
    "Santa Rosa, Lima, Peru",
    "Santiago de Surco, Lima, Peru",
    "Surquillo, Lima, Peru", 
    "Villa El Salvador, Lima, Peru",
    "Villa María del Triunfo, Lima, Peru",
    
    # --- CALLAO ---
    "Bellavista, Callao, Peru",
    "Callao District, Callao, Peru", 
    "Carmen de la Legua Reynoso, Callao, Peru",
    "La Perla, Callao, Peru", 
    "La Punta, Callao, Peru",
    "Mi Perú, Callao, Peru",
    "Ventanilla, Callao, Peru"
]

# Mapa de nombre OSM -> código ubigeo INEI
UBIGEO_MAP = {
    # --- LIMA ---
    "Ancón, Lima, Peru":                        "150102",
    "Ate, Lima, Peru":                          "150103",
    "Barranco, Lima, Peru":                     "150104",
    "Breña, Lima, Peru":                        "150105",
    "Carabayllo, Lima, Peru":                   "150106",
    "Chaclacayo, Lima, Peru":                   "150107",
    "Chorrillos, Lima, Peru":                   "150108",
    "Cieneguilla, Lima, Peru":                  "150109",
    "Comas, Lima, Peru":                        "150110",
    "El Agustino, Lima, Peru":                  "150111",
    "Independencia, Lima, Peru":                "150112",
    "Jesús María, Lima, Peru":                  "150113",
    "La Molina, Lima, Peru":                    "150114",
    "La Victoria, Lima, Peru":                  "150115",
    "Lima District, Lima, Peru":                "150101",
    "Lince, Lima, Peru":                        "150116",
    "Los Olivos, Lima, Peru":                   "150117",
    "Lurigancho, Lima, Peru":                   "150118",
    "Lurín, Lima, Peru":                        "150119",
    "Magdalena del Mar, Lima, Peru":            "150120",
    "Miraflores, Lima, Peru":                   "150122",
    "Pachacámac, Lima, Peru":                   "150123",
    "Pucusana, Lima, Peru":                     "150124",
    "Pueblo Libre, Lima, Peru":                 "150121",
    "Puente Piedra, Lima, Peru":                "150125",
    "Punta Hermosa, Lima, Peru":                "150126",
    "Punta Negra, Lima, Peru":                  "150127",
    "Rímac, Lima, Peru":                        "150128",
    "San Bartolo, Lima, Peru":                  "150129",
    "San Borja, Lima, Peru":                    "150130",
    "San Isidro, Lima, Peru":                   "150131",
    "San Juan de Lurigancho, Lima, Peru":       "150132",
    "San Juan de Miraflores, Lima, Peru":       "150133",
    "San Luis, Lima, Peru":                     "150134",
    "San Martín de Porres, Lima, Peru":         "150135",
    "San Miguel, Lima, Peru":                   "150136",
    "Santa Anita, Lima, Peru":                  "150137",
    "Santa María del Mar, Lima, Peru":          "150138",
    "Santa Rosa, Lima, Peru":                   "150139",
    "Santiago de Surco, Lima, Peru":            "150140",
    "Surquillo, Lima, Peru":                    "150141",
    "Villa El Salvador, Lima, Peru":            "150142",
    "Villa María del Triunfo, Lima, Peru":      "150143",

    # --- CALLAO ---
    "Bellavista, Callao, Peru":                 "070102",
    "Callao District, Callao, Peru":            "070101",
    "Carmen de la Legua Reynoso, Callao, Peru": "070103",
    "La Perla, Callao, Peru":                   "070104",
    "La Punta, Callao, Peru":                   "070105",
    "Mi Perú, Callao, Peru":                    "070107",
    "Ventanilla, Callao, Peru":                 "070106",
}

# Pesos del score compuesto
# Capas 1 y 2 forman el score base:
#   base = WEIGHT_DISTRICT * district_score + WEIGHT_CONTEXT * context_score
# La capa 3 (reportes ciudadanos validados) se mezcla SOLO donde existe
# al menos un reporte cercano, para no alterar el score del resto de la red:
#   composite = (1 - WEIGHT_REPORT) * base + WEIGHT_REPORT * report_score
WEIGHT_DISTRICT = 0.70    # Capa 1: criminalidad distrital
WEIGHT_CONTEXT  = 0.30    # Capa 2: contexto urbano
WEIGHT_REPORT   = 0.15    # Capa 3: reportes validados

# Capa 3: reportes validados 
# Valores propuestos por el equipo de desarrollo (no existe spec de BA);
# documentados en backend/DATABASE.md.
REPORT_INFLUENCE_RADIUS_M = 150   # ST_DWithin: radio de influencia de un reporte
REPORT_HALF_LIFE_DAYS = 90        # decaimiento exponencial: peso se reduce a la mitad cada 90 días
REPORT_MAX_AGE_DAYS = 365         # reportes más antiguos no aportan al score
REPORT_SATURATION = 3.0           # ~3 reportes recientes de peso máximo => riesgo máximo (1.0)

# Peso por tipo de incidente (0-1, mayor = más riesgoso para el peatón)
REPORT_TYPE_WEIGHTS = {
    "robo": 1.0,
    "asalto": 1.0,
    "violencia": 0.9,
    "acoso": 0.8,
    "droga": 0.7,
    "vandalismo": 0.5,
    "ocupacion_via": 0.3,
    "venta_ambulante": 0.3,
    "otro": 0.4,
}
REPORT_TYPE_WEIGHT_DEFAULT = 0.4

# Factor por severidad declarada (el aporte por reporte se capea a 1.0)
REPORT_SEVERITY_FACTOR = {
    "low": 0.5,
    "medium": 0.75,
    "high": 1.0,
    "critical": 1.25,
}
REPORT_SEVERITY_FACTOR_DEFAULT = 0.75

# Factor de aversión al riesgo para el Dijkstra
# cost(e) = length_m * (1 + ALPHA * composite_score)
ALPHA_RISK = 2.0

# Valor neutro cuando no hay datos de distrito o contexto
NEUTRAL_SCORE = 0.5

# Pesos de cada factor dentro del context_score
CONTEXT_WEIGHT_LIGHTING  = 0.30   # Factor 1: iluminación
CONTEXT_WEIGHT_POLICE    = 0.20   # Factor 2: presencia policial
CONTEXT_WEIGHT_ROAD_TYPE = 0.20   # Factor 3: tipo de vía
CONTEXT_WEIGHT_CAMERAS   = 0.15   # Factor 4: vigilancia (cámaras + bancos)
CONTEXT_WEIGHT_COMMERCE  = 0.15   # Factor 5: actividad comercial

# Riesgo por tipo de vía
HIGHWAY_RISK = {
    "primary":        0.20,
    "primary_link":   0.20,
    "secondary":      0.25,
    "secondary_link": 0.25,
    "pedestrian":     0.30,
    "tertiary":       0.35,
    "tertiary_link":  0.35,
    "living_street":  0.40,
    "residential":    0.45,
    "unclassified":   0.55,
    "service":        0.60,
    "footway":        0.70,
    "steps":          0.70,
    "path":           0.85,
    "track":          0.90,
}
HIGHWAY_RISK_DEFAULT = 0.50

# Umbrales de categorías 
CATEGORY_SAFE_THRESHOLD     = 70   # >= 70 -> "Segura"
CATEGORY_MODERATE_THRESHOLD = 40   # >= 40 -> "Moderada", < 40 -> "Riesgosa"

# Umbrales de composite_score por segmento (0-1)
RISK_LOW    = 0.30   # <= 0.30 -> verde
RISK_MEDIUM = 0.60   # <= 0.60 -> amarillo, > 0.60 -> rojo

# Regla de degradación: si más del 10% de la longitud es rojo, baja a Moderada
MAX_RED_FRACTION = 0.10

STREET_CRIMES = {
    "ROBO",
    "HOMICIDIO",
    "VIOLACION DE LA LIBERTAD SEXUAL",
    "VIOLACION DE LA LIBERTAD PERSONAL",
    "EXTORSION",
    "TRATA DE PERSONAS",
    "LESIONES",
    "HURTO",
    "PAZ PUBLICA",
    "PELIGRO COMUN",
    "DAÑOS",
    "EXPOSICION A PELIGRO O ABANDONO DE PERSONAS EN PELIGRO",
}

# Velocidad peatonal para calcular tiempo (5 km/h ≈ 83 m/min)
WALKING_SPEED_MPM = 83.0

# Distancia máxima permitida entre origen y destino (15 km en línea recta)
MAX_DISTANCE_M = 15_000

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