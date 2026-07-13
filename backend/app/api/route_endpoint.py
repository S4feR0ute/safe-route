from fastapi import APIRouter, Depends

from app.schemas.route_schemas import RouteRequest
from app.core.service_container import ServiceContainer, get_service_container
from app.core.constants import MAX_DISTANCE_M
from app.core.exceptions import ValidationError
from app.utils.geo import haversine_m

router = APIRouter(prefix="/api/v1", tags=["routing"])


@router.post("/route")
def calculate_route(
    request: RouteRequest,
    container: ServiceContainer = Depends(get_service_container)
):
    """Calcula la ruta peatonal más segura entre origen y destino."""
    straight_dist = haversine_m(
        request.origin.lat, request.origin.lon,
        request.destination.lat, request.destination.lon
    )

    if straight_dist < 50:
        raise ValidationError(
            "El origen y el destino son el mismo punto (menos de 50m)",
            details={"distancia_m": round(straight_dist, 1)},
        )

    if straight_dist > MAX_DISTANCE_M:
        raise ValidationError(
            f"Distancia máxima permitida: {MAX_DISTANCE_M / 1000:.0f} km",
            details={"distancia_m": round(straight_dist, 1)},
        )

    routing_service = container.get_routing_service()
    result = routing_service.calculate_routes(
        origin_lat=request.origin.lat,
        origin_lon=request.origin.lon,
        dest_lat=request.destination.lat,
        dest_lon=request.destination.lon,
    )
    return routing_service.build_route_response(result, request.include_shortest)
