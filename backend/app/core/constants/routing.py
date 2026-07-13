"""Parámetros del ruteo (Dijkstra ponderado por riesgo) y categorización de rutas."""

# Factor de aversión al riesgo para el Dijkstra
# cost(e) = length_m * (1 + ALPHA * composite_score)
ALPHA_RISK = 2.0

# Umbrales de categorías
CATEGORY_SAFE_THRESHOLD     = 70   # >= 70 -> "Segura"
CATEGORY_MODERATE_THRESHOLD = 40   # >= 40 -> "Moderada", < 40 -> "Riesgosa"

# Regla de degradación: si más del 10% de la longitud es rojo, baja a Moderada
MAX_RED_FRACTION = 0.10

# Velocidad peatonal para calcular tiempo (5 km/h ≈ 83 m/min)
WALKING_SPEED_MPM = 83.0

# Distancia máxima permitida entre origen y destino (15 km en línea recta)
MAX_DISTANCE_M = 15_000
