from pydantic import BaseModel

from app.schemas.export import ExportResponse
from app.schemas.geocode import GeocodedPoint
from app.schemas.optimize import OptimizationSummary, OptimizedPoint, OptimizedStartPoint


class ProcessRouteRequest(BaseModel):
    points: list[GeocodedPoint]


class ProcessRouteResponse(BaseModel):
    success: bool
    start_point: OptimizedStartPoint
    points: list[OptimizedPoint]
    optimization: OptimizationSummary
    export: ExportResponse
    error_message: str | None
