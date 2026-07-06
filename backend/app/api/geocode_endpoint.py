import logging
from fastapi import APIRouter, Depends

from app.schemas.geocode_schemas import GeocodeResponse, GeocodeResult
from app.core.service_container import ServiceContainer, get_service_container
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)
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
        return ErrorHandler.validation_error(
            message="Parámetro 'q' requerido",
            field="q"
        )

    try:
        raw_results = container.get_nominatim_service().search(q)

        results = [
            GeocodeResult(
                display_name=r["display_name"],
                lat=r["lat"],
                lon=r["lon"],
            )
            for r in raw_results
        ]
        return GeocodeResponse(results=results, total=len(results))

    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"Nominatim service unavailable: {e}")
        return ErrorHandler.service_unavailable(
            message="Servicio de geocodificación no disponible"
        )
    except Exception as e:
        logger.exception(f"Geocoding error: {type(e).__name__}")
        return ErrorHandler.internal_error(
            message="Error al procesar la búsqueda"
        )
