import logging
from fastapi import APIRouter

from app.schemas.geocode_schemas import GeocodeResponse, GeocodeResult
from app.services.nominatim_service import NominatimService
from app.core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["geocoding"])


@router.get("/geocode", response_model=GeocodeResponse)
def geocodificar(q: str):
    """
    Geocodificación de direcciones contra Nominatim (OpenStreetMap).
    """
    if not q or not q.strip():
        return ErrorHandler.validation_error(
            message="Parámetro 'q' requerido",
            field="q"
        )

    try:
        service = NominatimService()
        raw_results = service.buscar(q)

        if not raw_results:
            return GeocodeResponse(results=[], total=0)

        resultados = [
            GeocodeResult(
                display_name=r["display_name"],
                lat=r["lat"],
                lon=r["lon"],
            )
            for r in raw_results
        ]

        return GeocodeResponse(results=resultados, total=len(resultados))

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
