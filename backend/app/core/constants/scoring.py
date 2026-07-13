"""Parámetros del cálculo del composite_score (capas distrito / contexto / reportes)."""

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

# Umbrales de composite_score por segmento (0-1)
RISK_LOW    = 0.30   # <= 0.30 -> verde
RISK_MEDIUM = 0.60   # <= 0.60 -> amarillo, > 0.60 -> rojo
