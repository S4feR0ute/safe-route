from pydantic import BaseModel


class GeocodeRequest(BaseModel):
    q: str   # texto de búsqueda, ej: "Av. Larco, Miraflores"


class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float


class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]
    total: int
