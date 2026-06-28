from fastapi import APIRouter

from app.schemas.geocode_schemas import GeocodeResponse, GeocodeResult
from app.services.nominatim_service import NominatimService
from app.core.exceptions import error_response

router = APIRouter(prefix="/api/v1", tags=["geocoding"])


@router.get("/geocode")
def geocodificar(q: str):
    """
    Proxy de geocodificación contra Nominatim.
    Recibe un texto de búsqueda y devuelve hasta 5 candidatos
    dentro del área de Lima Metropolitana + Callao.
    """
    if not q or not q.strip():
        return error_response(
            code="INVALID_COORDINATES",
            message="El parámetro 'q' no puede estar vacío.",
            status_code=400
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

    except TimeoutError as e:
        return error_response(
            code="SERVICE_UNAVAILABLE",
            message=str(e),
            status_code=503
        )
    except ConnectionError as e:
        return error_response(
            code="SERVICE_UNAVAILABLE",
            message=str(e),
            status_code=503
        )
    except Exception:
        return error_response(
            code="INTERNAL_ERROR",
            message="Error al procesar la búsqueda. Intenta de nuevo.",
            status_code=500
        )
