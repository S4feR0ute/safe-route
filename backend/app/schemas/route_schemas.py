from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RouteRequest(BaseModel):
    origin:           Coordinate
    destination:      Coordinate
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
