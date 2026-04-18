import re
from typing import List

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.geocode import GeocodedPoint
from app.schemas.normalize import NormalizedPoint

logger = get_logger(__name__)

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GEOCODING_TIMEOUT = 10.0
ROUTE_START_POINT_ADDRESS = "Киев, Индустриальный переулок, 23"

BROAD_RESULT_TYPES = {
    "locality",
    "political",
    "administrative_area_level_1",
    "administrative_area_level_2",
    "country",
    "postal_code",
}
STRONG_RESULT_TYPES = {
    "street_address",
    "premise",
    "subpremise",
    "establishment",
}
BUILDING_COMPONENT_TYPES = {"street_number", "premise", "subpremise"}
ROUTE_COMPONENT_TYPES = {"route", "intersection"}
HOUSE_NUMBER_PATTERN = re.compile(r"\b\d+[A-Za-zА-Яа-яІіЇїЄє/\-]*\b")


class GeocodingService:
    """Service for geocoding normalized delivery points with Google Maps."""

    def _build_skipped_point(self, point: NormalizedPoint) -> GeocodedPoint:
        return GeocodedPoint(
            **point.model_dump(),
            formatted_address=None,
            lat=None,
            lng=None,
            geocode_status="skipped",
            geocode_precision="unknown",
        )

    def _build_error_point(
        self,
        point: NormalizedPoint,
        status: str,
        precision: str = "unknown",
    ) -> GeocodedPoint:
        payload = point.model_dump()
        if status == "not_found":
            payload["status"] = "skipped"

        return GeocodedPoint(
            **payload,
            formatted_address=None,
            lat=None,
            lng=None,
            geocode_status=status,
            geocode_precision=precision,
        )

    def _build_ok_point(
        self,
        point: NormalizedPoint,
        formatted_address: str,
        lat: float,
        lng: float,
        precision: str,
    ) -> GeocodedPoint:
        return GeocodedPoint(
            **point.model_dump(),
            formatted_address=formatted_address,
            lat=lat,
            lng=lng,
            geocode_status="ok",
            geocode_precision=precision,
        )

    def _input_expects_building(self, clean_address: str) -> bool:
        return bool(HOUSE_NUMBER_PATTERN.search(clean_address))

    def _extract_component_types(self, result: dict) -> set[str]:
        component_types: set[str] = set()
        for component in result.get("address_components", []):
            component_types.update(component.get("types", []))
        return component_types

    def evaluate_geocode_precision(self, clean_address: str, result: dict) -> str:
        result_types = set(result.get("types", []))
        component_types = self._extract_component_types(result)
        location_type = result.get("geometry", {}).get("location_type")

        broad_only = bool(result_types) and result_types.issubset(BROAD_RESULT_TYPES)
        plus_code_only = result_types == {"plus_code"}
        if broad_only or plus_code_only:
            return "too_general"

        has_building_component = bool(component_types & BUILDING_COMPONENT_TYPES)
        has_precise_result_type = bool(result_types & STRONG_RESULT_TYPES)
        has_route = bool(result_types & ROUTE_COMPONENT_TYPES) or bool(
            component_types & ROUTE_COMPONENT_TYPES
        )

        if self._input_expects_building(clean_address) and not has_building_component:
            return "too_general"

        if location_type == "ROOFTOP" and (
            has_building_component or has_precise_result_type
        ):
            return "exact"

        if has_building_component or has_precise_result_type or has_route:
            return "acceptable"

        if location_type in {"GEOMETRIC_CENTER", "APPROXIMATE"}:
            return "too_general"

        return "unknown"

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
            "exact": 0,
            "acceptable": 0,
            "downgraded": 0,
            "not_found": 0,
            "skipped": 0,
            "error": 0,
        }
        rejected_examples: list[str] = []

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
                        if len(rejected_examples) < 3:
                            rejected_examples.append(point.clean_address)
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
                    precision = self.evaluate_geocode_precision(
                        point.clean_address,
                        first_result,
                    )

                    if formatted_address is None or lat is None or lng is None:
                        raise ValueError("Incomplete geocoding response payload")

                    if precision == "too_general":
                        geocoded_points.append(
                            self._build_error_point(
                                point,
                                "not_found",
                                precision="too_general",
                            )
                        )
                        stats["downgraded"] += 1
                        if len(rejected_examples) < 3:
                            rejected_examples.append(point.clean_address)
                        continue

                    geocoded_points.append(
                        self._build_ok_point(
                            point,
                            formatted_address,
                            lat,
                            lng,
                            precision=precision,
                        )
                    )
                    if precision == "exact":
                        stats["exact"] += 1
                    else:
                        stats["acceptable"] += 1
                except Exception:
                    logger.exception(
                        "Geocoding failed for address '%s'",
                        point.clean_address,
                    )
                    geocoded_points.append(self._build_error_point(point, "error"))
                    stats["error"] += 1

        log_message = (
            "Points geocoded | total_points=%s exact=%s acceptable=%s downgraded=%s not_found=%s skipped=%s errors=%s"
        )
        if rejected_examples:
            log_message += " rejected_examples=%s"
            logger.info(
                log_message,
                len(points),
                stats["exact"],
                stats["acceptable"],
                stats["downgraded"],
                stats["not_found"],
                stats["skipped"],
                stats["error"],
                rejected_examples,
            )
        else:
            logger.info(
                log_message,
                len(points),
                stats["exact"],
                stats["acceptable"],
                stats["downgraded"],
                stats["not_found"],
                stats["skipped"],
                stats["error"],
            )

        return geocoded_points
