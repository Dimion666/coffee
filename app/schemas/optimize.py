from typing import Literal

from pydantic import BaseModel

from app.schemas.geocode import GeocodedPoint


class OptimizeRequest(BaseModel):
    points: list[GeocodedPoint]


class OptimizedStartPoint(BaseModel):
    address: str
    lat: float | None
    lng: float | None


class OptimizedPoint(GeocodedPoint):
    route_order: int | None


class OptimizationSummary(BaseModel):
    total_input_points: int
    eligible_points: int
    excluded_points: int
    mode: Literal["google_routes_api"]
    success: bool
    error_message: str | None


class OptimizedRouteResult(BaseModel):
    start_point: OptimizedStartPoint
    points: list[OptimizedPoint]
    optimization: OptimizationSummary
