import logging
from fastapi import APIRouter, Depends

from app.schemas.route_schemas import RouteRequest
from app.core.service_container import ServiceContainer, get_service_container
from app.core.constants import MAX_DISTANCE_M
from app.core.error_handler import ErrorHandler
from app.core.exceptions import EmptyGraphError, NoRouteError, NodeNotFoundError
from app.utils.geo import haversine_m

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["routing"])


@router.post("/route")
def calculate_route(
    request: RouteRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """
    Calcula la ruta peatonal más segura entre origen y destino.
    """
    straight_dist = haversine_m(
        request.origin.lat, request.origin.lon,
        request.destination.lat, request.destination.lon
    )

    if straight_dist < 50:
        return ErrorHandler.validation_error(
            message="El origen y el destino son el mismo punto (menos de 50m)",
            details={"distancia_m": round(straight_dist, 1)}
        )

    if straight_dist > MAX_DISTANCE_M:
        return ErrorHandler.validation_error(
            message=f"Distancia máxima permitida: {MAX_DISTANCE_M/1000:.0f} km",
            details={"distancia_m": round(straight_dist, 1)}
        )

    try:
        routing_service = container.get_routing_service()
        result = routing_service.calculate_routes(
            origin_lat=request.origin.lat,
            origin_lon=request.origin.lon,
            dest_lat=request.destination.lat,
            dest_lon=request.destination.lon,
        )
        return routing_service.build_route_response(result, request.include_shortest)

    except EmptyGraphError:
        return ErrorHandler.service_unavailable(
            message="Los datos de rutas no han sido inicializados"
        )
    except (NoRouteError, NodeNotFoundError):
        return ErrorHandler.not_found("No existe una ruta peatonal disponible")
    except Exception as e:
        logger.exception(f"Route calculation error: {type(e).__name__}")
        return ErrorHandler.internal_error(message="Error al calcular la ruta")
