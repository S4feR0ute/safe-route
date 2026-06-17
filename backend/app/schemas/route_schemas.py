from pydantic import BaseModel, validator


class Coordenada(BaseModel):
    lat: float
    lon: float

    @validator("lat")
    def validar_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("lat debe estar entre -90 y 90")
        return v

    @validator("lon")
    def validar_lon(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("lon debe estar entre -180 y 180")
        return v


class RouteRequest(BaseModel):
    origin:           Coordenada
    destination:      Coordenada
    include_shortest: bool = True


class RouteSummary(BaseModel):
    distance_m:     float
    walk_time_min:  int
    security_score: int
    category:       str


class RouteResult(BaseModel):
    summary: RouteSummary
    geojson: dict


class ComparisonResult(BaseModel):
    extra_distance_m:    float
    extra_time_min:      int
    risk_reduction_pct:  float


class RouteResponse(BaseModel):
    safe_route:     RouteResult
    shortest_route: RouteResult | None = None
    comparison:     ComparisonResult | None = None


class ErrorDetail(BaseModel):
    code:    str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail
