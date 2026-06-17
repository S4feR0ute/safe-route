from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.geocode_schemas import GeocodeResponse, GeocodeResult
from app.services.nominatim_service import NominatimService

router = APIRouter(prefix="/api/v1", tags=["geocoding"])


@router.get("/geocode")
def geocodificar(q: str):
    """
    Proxy de geocodificación contra Nominatim (RF-06).
    Recibe un texto de búsqueda y devuelve hasta 5 candidatos
    dentro del área de Lima Metropolitana + Callao.

    Ejemplo:
        GET /api/v1/geocode?q=Av.+Larco+Miraflores
    """
    if not q or not q.strip():
        return JSONResponse(status_code=400, content={"error": {
            "code": "INVALID_COORDINATES",
            "message": "El parámetro 'q' no puede estar vacío.",
            "details": {}
        }})

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
        return JSONResponse(status_code=503, content={"error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": str(e),
            "details": {}
        }})
    except ConnectionError as e:
        return JSONResponse(status_code=503, content={"error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": str(e),
            "details": {}
        }})
    except Exception:
        return JSONResponse(status_code=500, content={"error": {
            "code": "INTERNAL_ERROR",
            "message": "Error al procesar la búsqueda. Intenta de nuevo.",
            "details": {}
        }})
