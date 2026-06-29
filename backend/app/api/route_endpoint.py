import math
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.route_schemas import RouteRequest, RouteResponse
from app.core.service_container import ServiceContainer, get_service_container
from app.core.constants import RIESGO_BAJO, RIESGO_MEDIO, VELOCIDAD_PEATONAL_MPM, DISTANCIA_MAXIMA_M
from app.core.error_handler import ErrorHandler
from app.core.exceptions import EmptyGraphError, NoRouteError, NodeNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["routing"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Verificación de vida del servicio."""
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return ErrorHandler.service_unavailable(
            message="La base de datos no está disponible"
        )


@router.post("/route")
def calcular_ruta(
    request: RouteRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Calcula la ruta peatonal más segura entre origen y destino.
    """
    dist_lineal = _distancia_metros(
        request.origin.lat, request.origin.lon,
        request.destination.lat, request.destination.lon
    )

    if dist_lineal < 50:
        return ErrorHandler.validation_error(
            message="El origen y el destino son el mismo punto (menos de 50m)",
            details={"distancia_m": round(dist_lineal, 1)}
        )

    if dist_lineal > DISTANCIA_MAXIMA_M:
        return ErrorHandler.validation_error(
            message=f"Distancia máxima permitida: {DISTANCIA_MAXIMA_M/1000:.0f} km",
            details={"distancia_m": round(dist_lineal, 1)}
        )

    try:
        routing_service = container.get_routing_service()
        resultado = routing_service.calcular_rutas(
            origen_lat=request.origin.lat,
            origen_lon=request.origin.lon,
            destino_lat=request.destination.lat,
            destino_lon=request.destination.lon,
        )
    except EmptyGraphError:
        return ErrorHandler.service_unavailable(
            message="Los datos de rutas no han sido inicializados"
        )
    except (NoRouteError, NodeNotFoundError):
        return ErrorHandler.not_found("No existe una ruta peatonal disponible")
    except Exception as e:
        logger.exception(f"Route calculation error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al calcular la ruta"
        )

    ruta_segura = resultado["ruta_segura"]
    ruta_corta  = resultado["ruta_corta"]

    safe_geojson = _build_geojson(ruta_segura["segmentos"])
    safe_summary = _build_summary(ruta_segura)

    response = {
        "safe_route": {
            "summary": safe_summary,
            "geojson": safe_geojson,
        },
        "shortest_route": None,
        "comparison": None,
    }

    if request.include_shortest:
        short_geojson = _build_geojson(ruta_corta["segmentos"])
        short_summary = _build_summary(ruta_corta)

        response["shortest_route"] = {
            "summary": short_summary,
            "geojson": short_geojson,
        }
        response["comparison"] = _build_comparison(ruta_segura, ruta_corta)

    return response


def _build_geojson(segmentos: list) -> dict:
    """
    Convierte la lista de segmentos en un GeoJSON FeatureCollection.
    Un Feature por segmento para que el frontend pueda colorear cada tramo.
    """
    features = []
    for seg in segmentos:
        color = _color_por_score(seg["composite_score"])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": seg["coordinates"],
            },
            "properties": {
                "name":       seg["name"],
                "length_m":   round(seg["length_m"], 2),
                "risk_score": round(seg["composite_score"], 4),
                "color":      color,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _build_summary(ruta: dict) -> dict:
    """Arma el summary de una ruta con distancia, tiempo y score."""
    dist = ruta["longitud_total_m"]
    walk_time = math.ceil(dist / VELOCIDAD_PEATONAL_MPM)
    return {
        "distance_m":     round(dist, 2),
        "walk_time_min":  walk_time,
        "security_score": ruta["security_score"],
        "category":       ruta["categoria"],
    }


def _build_comparison(ruta_segura: dict, ruta_corta: dict) -> dict:
    """
    Calcula las diferencias entre la ruta segura y la corta.
    risk_reduction_pct: reducción porcentual del riesgo promedio (SAF-45).
    """
    extra_m = ruta_segura["longitud_total_m"] - ruta_corta["longitud_total_m"]
    extra_min = math.ceil(abs(extra_m) / VELOCIDAD_PEATONAL_MPM)

    riesgo_segura = 1 - (ruta_segura["security_score"] / 100)
    riesgo_corta  = 1 - (ruta_corta["security_score"] / 100)

    if riesgo_corta > 0:
        reduccion_pct = round(((riesgo_corta - riesgo_segura) / riesgo_corta) * 100, 1)
    else:
        reduccion_pct = 0.0

    return {
        "extra_distance_m":   round(extra_m, 2),
        "extra_time_min":     extra_min,
        "risk_reduction_pct": reduccion_pct,
    }


def _color_por_score(composite_score: float) -> str:
    """Devuelve el color hex del segmento según su composite_score (SAF-44)."""
    if composite_score <= RIESGO_BAJO:
        return "#2E7D32"   # verde
    elif composite_score <= RIESGO_MEDIO:
        return "#F9A825"   # amarillo
    else:
        return "#C62828"   # rojo


def _distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distancia en metros entre dos coordenadas usando la fórmula de Haversine.
    Suficientemente precisa para las validaciones de rango.
    """
    R = 6_371_000  # radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
