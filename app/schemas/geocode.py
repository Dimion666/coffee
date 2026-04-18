from typing import Literal

from pydantic import BaseModel

from app.schemas.normalize import NormalizedPoint


class GeocodeRequest(BaseModel):
    points: list[NormalizedPoint]


class GeocodedPoint(NormalizedPoint):
    formatted_address: str | None
    lat: float | None
    lng: float | None
    geocode_status: Literal["ok", "not_found", "skipped", "error"]
    geocode_precision: Literal["exact", "acceptable", "too_general", "unknown"]


class StartPoint(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    points: list[GeocodedPoint]
    start_point: StartPoint
