from fastapi import APIRouter, Depends

from app.schemas.geocode_schemas import GeocodeResponse, GeocodeResult
from app.core.service_container import ServiceContainer, get_service_container
from app.core.exceptions import ValidationError, ServiceUnavailableError

router = APIRouter(prefix="/api/v1", tags=["geocoding"])


@router.get("/geocode", response_model=GeocodeResponse)
def geocode(
    q: str,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Geocodificación de direcciones contra Nominatim (OpenStreetMap).
    """
    if not q or not q.strip():
        raise ValidationError("Parámetro 'q' requerido", details={"field": "q"})

    try:
        raw_results = container.get_nominatim_service().search(q)
    except (TimeoutError, ConnectionError) as e:
        raise ServiceUnavailableError(
            "Servicio de geocodificación no disponible"
        ) from e

    results = [
        GeocodeResult(
            display_name=r["display_name"],
            lat=r["lat"],
            lon=r["lon"],
        )
        for r in raw_results
    ]
    return GeocodeResponse(results=results, total=len(results))
