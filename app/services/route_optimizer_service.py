from typing import List

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.geocode import GeocodedPoint
from app.schemas.optimize import (
    OptimizationSummary,
    OptimizedPoint,
    OptimizedRouteResult,
    OptimizedStartPoint,
)
from app.services.geocoding_service import GeocodingService, ROUTE_START_POINT_ADDRESS

logger = get_logger(__name__)

ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
ROUTES_API_TIMEOUT = 20.0
ROUTES_API_FIELD_MASK = "routes.optimizedIntermediateWaypointIndex"


class RouteOptimizerService:
    """Single-vehicle route optimization using Google Routes API."""

    def __init__(self, geocoding_service: GeocodingService | None = None) -> None:
        self.geocoding_service = geocoding_service or GeocodingService()

    def _is_eligible(self, point: GeocodedPoint) -> bool:
        return (
            point.status == "valid"
            and not point.is_crossed
            and point.geocode_status == "ok"
            and point.lat is not None
            and point.lng is not None
        )

    def _build_waypoint(self, lat: float, lng: float) -> dict:
        return {
            "location": {
                "latLng": {
                    "latitude": lat,
                    "longitude": lng,
                }
            }
        }

    def _build_result(
        self,
        points: List[OptimizedPoint],
        start_address: str,
        start_lat: float | None,
        start_lng: float | None,
        total_input_points: int,
        eligible_points: int,
        success: bool,
        error_message: str | None,
    ) -> OptimizedRouteResult:
        return OptimizedRouteResult(
            start_point=OptimizedStartPoint(
                address=start_address,
                lat=start_lat,
                lng=start_lng,
            ),
            points=points,
            optimization=OptimizationSummary(
                total_input_points=total_input_points,
                eligible_points=eligible_points,
                excluded_points=total_input_points - eligible_points,
                mode="google_routes_api",
                success=success,
                error_message=error_message,
            ),
        )

    def _geocode_start_point(self, start_address: str) -> dict:
        return self.geocoding_service.geocode_address(start_address)

    def _request_optimized_order(
        self,
        client: httpx.Client,
        start_lat: float,
        start_lng: float,
        eligible_points: List[GeocodedPoint],
    ) -> list[int]:
        response = client.post(
            ROUTES_API_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
                "X-Goog-FieldMask": ROUTES_API_FIELD_MASK,
            },
            json={
                "origin": self._build_waypoint(start_lat, start_lng),
                "destination": self._build_waypoint(start_lat, start_lng),
                "intermediates": [
                    self._build_waypoint(point.lat, point.lng)
                    for point in eligible_points
                    if point.lat is not None and point.lng is not None
                ],
                "travelMode": "DRIVE",
                "optimizeWaypointOrder": True,
                "languageCode": "uk",
                "regionCode": "ua",
            },
        )
        response.raise_for_status()
        data = response.json()
        routes = data.get("routes", [])
        if not routes:
            raise ValueError("Routes API returned no routes.")

        optimized_indexes = routes[0].get("optimizedIntermediateWaypointIndex")
        if optimized_indexes is None:
            raise ValueError("Routes API returned no optimized waypoint order.")

        if len(optimized_indexes) != len(eligible_points):
            raise ValueError("Routes API returned an unexpected waypoint count.")

        return optimized_indexes

    def optimize_route(
        self,
        points: List[GeocodedPoint],
        start_address: str = ROUTE_START_POINT_ADDRESS,
    ) -> OptimizedRouteResult:
        optimized_points = [
            OptimizedPoint(**point.model_dump(), route_order=None) for point in points
        ]
        eligible_indices = [
            index for index, point in enumerate(points) if self._is_eligible(point)
        ]
        eligible_points = [points[index] for index in eligible_indices]

        start_lat: float | None = None
        start_lng: float | None = None
        start_geocoded = False
        start_error_message: str | None = None

        try:
            start_result = self._geocode_start_point(start_address)
            if (
                start_result["geocode_status"] == "ok"
                and start_result["lat"] is not None
                and start_result["lng"] is not None
            ):
                start_lat = start_result["lat"]
                start_lng = start_result["lng"]
                start_geocoded = True
        except Exception as exc:
            logger.exception("Failed to geocode start point '%s'", start_address)
            start_error_message = str(exc)

        logger.info(
            "Route optimization preparation | total_input=%s eligible=%s excluded=%s start_point_geocoded=%s",
            len(points),
            len(eligible_points),
            len(points) - len(eligible_points),
            "yes" if start_geocoded else "no",
        )

        if not eligible_points:
            return self._build_result(
                optimized_points,
                start_address,
                start_lat,
                start_lng,
                total_input_points=len(points),
                eligible_points=0,
                success=True,
                error_message=None,
            )

        if not start_geocoded:
            error_message = start_error_message or "Failed to geocode fixed start point."
            logger.warning("Routes API skipped because start point is unavailable.")
            return self._build_result(
                optimized_points,
                start_address,
                start_lat,
                start_lng,
                total_input_points=len(points),
                eligible_points=len(eligible_points),
                success=False,
                error_message=error_message,
            )

        if len(eligible_points) == 1:
            optimized_points[eligible_indices[0]].route_order = 1
            logger.info("Routes API skipped because only one eligible point is present.")
            return self._build_result(
                optimized_points,
                start_address,
                start_lat,
                start_lng,
                total_input_points=len(points),
                eligible_points=1,
                success=True,
                error_message=None,
            )

        try:
            with httpx.Client(timeout=ROUTES_API_TIMEOUT) as client:
                optimized_order = self._request_optimized_order(
                    client,
                    start_lat,
                    start_lng,
                    eligible_points,
                )

            for route_order, optimized_index in enumerate(optimized_order, start=1):
                original_index = eligible_indices[optimized_index]
                optimized_points[original_index].route_order = route_order

            logger.info("Routes API optimization completed successfully.")
            return self._build_result(
                optimized_points,
                start_address,
                start_lat,
                start_lng,
                total_input_points=len(points),
                eligible_points=len(eligible_points),
                success=True,
                error_message=None,
            )
        except Exception as exc:
            logger.exception("Routes API optimization failed.")
            return self._build_result(
                optimized_points,
                start_address,
                start_lat,
                start_lng,
                total_input_points=len(points),
                eligible_points=len(eligible_points),
                success=False,
                error_message=str(exc),
            )
