from typing import List

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.geocode import GeocodedPoint
from app.schemas.normalize import NormalizedPoint

logger = get_logger(__name__)

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GEOCODING_TIMEOUT = 10.0


class GeocodingService:
    """Service for geocoding normalized delivery points with Google Maps."""

    def _build_skipped_point(self, point: NormalizedPoint) -> GeocodedPoint:
        return GeocodedPoint(
            **point.model_dump(),
            formatted_address=None,
            lat=None,
            lng=None,
            geocode_status="skipped",
        )

    def _build_error_point(self, point: NormalizedPoint, status: str) -> GeocodedPoint:
        payload = point.model_dump()
        if status == "not_found":
            payload["status"] = "skipped"

        return GeocodedPoint(
            **payload,
            formatted_address=None,
            lat=None,
            lng=None,
            geocode_status=status,
        )

    def _build_ok_point(
        self,
        point: NormalizedPoint,
        formatted_address: str,
        lat: float,
        lng: float,
    ) -> GeocodedPoint:
        return GeocodedPoint(
            **point.model_dump(),
            formatted_address=formatted_address,
            lat=lat,
            lng=lng,
            geocode_status="ok",
        )

    def _geocode_address(self, client: httpx.Client, clean_address: str) -> dict:
        response = client.get(
            GEOCODING_URL,
            params={
                "address": clean_address,
                "key": settings.GOOGLE_MAPS_API_KEY,
                "language": "uk",
                "region": "ua",
            },
        )
        response.raise_for_status()
        return response.json()

    def geocode_points(self, points: List[NormalizedPoint]) -> List[GeocodedPoint]:
        geocoded_points: List[GeocodedPoint] = []
        stats = {
            "ok": 0,
            "not_found": 0,
            "skipped": 0,
            "error": 0,
        }
        not_found_examples: list[str] = []

        with httpx.Client(timeout=GEOCODING_TIMEOUT) as client:
            for point in points:
                if point.status != "valid" or point.is_crossed:
                    geocoded_points.append(self._build_skipped_point(point))
                    stats["skipped"] += 1
                    continue

                try:
                    data = self._geocode_address(client, point.clean_address)
                    api_status = data.get("status")
                    results = data.get("results", [])

                    if api_status == "ZERO_RESULTS":
                        geocoded_points.append(self._build_error_point(point, "not_found"))
                        stats["not_found"] += 1
                        if len(not_found_examples) < 3:
                            not_found_examples.append(point.clean_address)
                        continue

                    if api_status != "OK" or not results:
                        raise ValueError(
                            f"Unexpected geocoding response status: {api_status}"
                        )

                    first_result = results[0]
                    location = first_result.get("geometry", {}).get("location", {})
                    formatted_address = first_result.get("formatted_address")
                    lat = location.get("lat")
                    lng = location.get("lng")

                    if formatted_address is None or lat is None or lng is None:
                        raise ValueError("Incomplete geocoding response payload")

                    geocoded_points.append(
                        self._build_ok_point(point, formatted_address, lat, lng)
                    )
                    stats["ok"] += 1
                except Exception:
                    logger.exception(
                        "Geocoding failed for address '%s'",
                        point.clean_address,
                    )
                    geocoded_points.append(self._build_error_point(point, "error"))
                    stats["error"] += 1

        log_message = (
            "Points geocoded | total_points=%s ok=%s not_found=%s skipped=%s errors=%s"
        )
        if not_found_examples:
            log_message += " not_found_examples=%s"
            logger.info(
                log_message,
                len(points),
                stats["ok"],
                stats["not_found"],
                stats["skipped"],
                stats["error"],
                not_found_examples,
            )
        else:
            logger.info(
                log_message,
                len(points),
                stats["ok"],
                stats["not_found"],
                stats["skipped"],
                stats["error"],
            )

        return geocoded_points
