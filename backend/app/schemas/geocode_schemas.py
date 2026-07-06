from pydantic import BaseModel


class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float


class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]
    total: int
